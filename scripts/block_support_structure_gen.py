#!/usr/bin/env python3

"""Command-line utility for generating block support structures."""

import argparse
import logging
import sys
from pathlib import Path
from typing import Any, Sequence

import trimesh
import trimesh.exchange.gltf

import pyslm.support
from pyslm.core import Part


def parse_rotation(value: str) -> list[float]:
    """Convert comma-separated Euler rotations into a float triplet."""

    parts = [chunk.strip() for chunk in value.split(",") if chunk.strip()]
    if len(parts) != 3:
        raise argparse.ArgumentTypeError(
            "Rotation must contain three comma-separated values, e.g. 62,50,0."
        )
    try:
        return [float(part) for part in parts]
    except ValueError as exc:
        raise argparse.ArgumentTypeError(
            "Rotation values must be numeric, e.g. 62,50,0."
        ) from exc


def parse_args(argv: list[str]) -> argparse.Namespace:
    """Parse command-line arguments for the block support generator."""

    parser = argparse.ArgumentParser(
        description="Generate solid block supports for an input STL using PySLM."
    )
    parser.add_argument(
        "input_stl",
        type=Path,
        help="Path to the input STL file representing the part geometry.",
    )
    parser.add_argument(
        "output_glb",
        type=Path,
        help="Destination path for the generated support GLB file.",
    )
    parser.add_argument(
        "--show",
        action="store_true",
        help="Display the generated supports and part geometry using trimesh.",
    )

    parser.add_argument(
        "--overhang-angle",
        type=float,
        default=55.0,
        help="Overhang angle in degrees used to detect unsupported regions (default: 55).",
    )
    parser.add_argument(
        "--ray-resolution",
        type=float,
        default=0.05,
        help="Ray projection resolution in mm for the height-map (default: 0.05).",
    )
    parser.add_argument(
        "--inner-gap",
        type=float,
        default=0.3,
        help="Inner support edge gap in mm between adjacent regions (default: 0.3).",
    )
    parser.add_argument(
        "--outer-gap",
        type=float,
        default=0.3,
        help="Outer support edge gap in mm near overhang boundaries (default: 0.3).",
    )
    parser.add_argument(
        "--simplify-factor",
        type=float,
        default=0.5,
        help="Factor used when simplifying polygon boundaries (default: 0.5).",
    )
    parser.add_argument(
        "--triangulation-spacing",
        type=float,
        default=2.0,
        help="Triangulation spacing in mm for extruded polygons (default: 2.0).",
    )
    parser.add_argument(
        "--min-area",
        type=float,
        default=0.1,
        help="Minimum support region area in mm^2 to process (default: 0.1).",
    )
    parser.add_argument(
        "--spline-factor",
        type=float,
        default=10.0,
        help="Spline simplification factor applied to support boundaries (default: 10).",
    )

    parser.add_argument(
        "--drop-height",
        type=float,
        default=10.0,
        help="Offset in mm applied when dropping the part to the build platform (default: 10).",
    )
    parser.add_argument(
        "--rotation",
        type=parse_rotation,
        metavar="RX,RY,RZ",
        default=[0, 0, 0],
        help="Euler rotations in degrees as comma-separated values (default: 62,50,0).",
    )

    return parser.parse_args(argv)


def configure_part(
    stl_path: Path, drop_height: float, rotation: Sequence[float]
) -> Part:
    """Load the STL into a Part, apply rotation, and drop it onto the build platform."""

    part = Part("block_support_part")
    part.setGeometry(str(stl_path), fixGeometry=True)
    part.scaleFactor = 1.0
    part.rotation = list(rotation)
    part.dropToPlatform(drop_height)
    return part


def configure_generator(
    args: argparse.Namespace,
) -> pyslm.support.BlockSupportGenerator:
    """Create and configure the support generator from CLI arguments."""

    generator = pyslm.support.BlockSupportGenerator()
    generator.overhangAngle = args.overhang_angle
    generator.rayProjectionResolution = args.ray_resolution
    generator.innerSupportEdgeGap = args.inner_gap
    generator.outerSupportEdgeGap = args.outer_gap
    generator.simplifyPolygonFactor = args.simplify_factor
    generator.triangulationSpacing = args.triangulation_spacing
    generator.minimumAreaThreshold = args.min_area
    generator.splineSimplificationFactor = args.spline_factor
    return generator


def export_supports(meshes: list[trimesh.Trimesh], output_path: Path) -> None:
    """Export generated support meshes to GLB format."""

    output_path.parent.mkdir(parents=True, exist_ok=True)
    scene = trimesh.Scene(meshes)
    export_glb: Any = getattr(trimesh.exchange.gltf, "export_glb")
    glb_bytes = export_glb(scene, include_normals=True)
    with output_path.open("wb") as fh:
        fh.write(glb_bytes)


def maybe_show_scene(
    part: Part,
    support_meshes: list[trimesh.Trimesh],
    overhang_angle: float,
) -> None:
    """Display the part, overhang mesh, and generated supports if requested."""

    overhang_mesh = pyslm.support.getOverhangMesh(
        part, overhang_angle, splitMesh=False, useConnectivity=True
    )
    display_scene = trimesh.Scene([part.geometry, overhang_mesh] + support_meshes)
    show_fn: Any = getattr(display_scene, "show")
    show_fn()


def main(argv: list[str]) -> int:
    args = parse_args(argv)

    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    if not args.input_stl.is_file():
        logging.error("Input STL not found: %s", args.input_stl)
        return 1

    try:
        part = configure_part(args.input_stl, args.drop_height, args.rotation)
    except Exception:
        logging.exception("Failed to load part geometry from %s", args.input_stl)
        return 1

    generator = configure_generator(args)

    logging.info(
        "Identifying block support regions (overhang %.2f°)", args.overhang_angle
    )
    support_regions = generator.identifySupportRegions(part, args.overhang_angle, True)
    support_meshes = [
        region.supportVolume for region in support_regions if region.supportVolume
    ]

    if not support_meshes:
        logging.warning("No support regions were generated; nothing to export.")
        return 0

    try:
        export_supports(support_meshes, args.output_glb)
    except Exception:
        logging.exception("Failed to write support GLB to %s", args.output_glb)
        return 1

    logging.info("Support GLB written to %s", args.output_glb)

    if args.show:
        try:
            maybe_show_scene(part, support_meshes, args.overhang_angle)
        except Exception:
            logging.exception("Failed to display support scene")

    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
