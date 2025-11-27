#!/usr/bin/env python3
"""
Convert GLB (GLTF Binary) files to STL format.
Requires: trimesh, numpy
Install with: pip install trimesh numpy
"""

import argparse
import sys
from pathlib import Path

try:
    import trimesh
except ImportError:
    print("Error: trimesh library not found. Install it with: pip install trimesh")
    sys.exit(1)


def glb_to_stl(input_path: str, output_path: str = None) -> None:
    """
    Convert a GLB file to STL format.
    
    Args:
        input_path: Path to input GLB file
        output_path: Path to output STL file (optional, defaults to same name with .stl)
    """
    input_file = Path(input_path)
    
    if not input_file.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    if not input_file.suffix.lower() in ['.glb', '.gltf']:
        raise ValueError(f"Input file must be GLB or GLTF format: {input_path}")
    
    # Determine output path
    if output_path is None:
        output_file = input_file.with_suffix('.stl')
    else:
        output_file = Path(output_path)
    
    print(f"Loading GLB file: {input_file}")
    
    # Load the GLB file
    mesh = trimesh.load(str(input_file))
    
    # If the result is a Scene (multiple meshes), combine them
    if isinstance(mesh, trimesh.Scene):
        print(f"Scene contains {len(mesh.geometry)} meshes, combining...")
        mesh = trimesh.util.concatenate(
            [geom for geom in mesh.geometry.values() if isinstance(geom, trimesh.Trimesh)]
        )
    
    # Export to STL
    print(f"Exporting to STL: {output_file}")
    mesh.export(str(output_file))
    
    print(f"✓ Conversion successful!")
    print(f"  Vertices: {len(mesh.vertices)}")
    print(f"  Faces: {len(mesh.faces)}")


def main():
    parser = argparse.ArgumentParser(
        description="Convert GLB files to STL format",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s model.glb
  %(prog)s model.glb -o output.stl
  %(prog)s input.glb --output converted.stl
        """
    )
    
    parser.add_argument(
        'input',
        help='Input GLB file path'
    )
    
    parser.add_argument(
        '-o', '--output',
        help='Output STL file path (default: same name as input with .stl extension)',
        default=None
    )
    
    args = parser.parse_args()
    
    try:
        glb_to_stl(args.input, args.output)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
