"""
Support generation script - Shows how to generate basic block supports using PySLM
This example uses BlockSupportGenerator to generate solid block supports.
"""

import logging

import numpy as np
import trimesh
import trimesh.creation
import trimesh.exchange.gltf
import trimesh.exchange.stl

import pyslm.support
import pyslm.visualise
from pyslm.core import Part
from pyslm.geometry import ContourGeometry, Layer

"""
Uncomment the line below to provide debug messages for OpenGL - if issues arise.
"""
# vispy.set_log_level('debug')

logging.getLogger().setLevel(logging.INFO)

## CONSTANTS ####
OVERHANG_ANGLE = 55  # deg - Overhang angle

"""
Set the Geometry for the Example using a complicated topology optimised bracket geometry
"""
myPart = Part("myPart")
# myPart.setGeometry("../models/bracket.stl", fixGeometry=True)
myPart.setGeometry("../models/frameGuide.stl", fixGeometry=True)

myPart.rotation = [
    62.0,
    50.0,
    -0.0,
]

myPart.scaleFactor = 1.0
myPart.dropToPlatform(10)

""" Extract the overhang mesh - don't explicitly split the mesh"""
overhangMesh = pyslm.support.getOverhangMesh(
    myPart, OVERHANG_ANGLE, splitMesh=False, useConnectivity=True
)

overhangMesh.visual.face_colors = [254.0, 0.0, 0.0, 254]

"""
Generate the geometry for the supports (Point and Edge Over Hangs)
"""
# First generate point and edge supports
pointOverhangs = pyslm.support.BaseSupportGenerator.findOverhangPoints(myPart)
overhangEdges = pyslm.support.BaseSupportGenerator.findOverhangEdges(myPart)

"""
Generate block supports for the part.

The BlockSupportGenerator class is initialised and the parameters below are specified as a reasonable starting
defaults for the algorithm. This generates solid block support volumes.
"""
supportGenerator = pyslm.support.BlockSupportGenerator()
supportGenerator.rayProjectionResolution = (
    0.05  # [mm] - The resolution of the grid used for the ray projection
)
supportGenerator.innerSupportEdgeGap = (
    0.3  # [mm] - Inner support offset used between adjacent support distances
)
supportGenerator.outerSupportEdgeGap = (
    0.3  # [mm] - Outer support offset used for the boundaries of overhang regions
)
supportGenerator.simplifyPolygonFactor = (
    0.5  #      - Factor used for simplifying the overall support shape
)
supportGenerator.triangulationSpacing = (
    2.0  # [mm] - Used for triangulating the extruded polygon for the bloc
)
supportGenerator.minimumAreaThreshold = (
    0.1  # Minimum area threshold to not process support region'
)

supportGenerator.splineSimplificationFactor = 10  # - Specify the smoothing factor using spline interpolation for the support boundaries

"""
Generate a list of Block Supports (trimesh objects currently). The contain the support volumes and other generated
information identified from the support surfaces identified on the part based on the choice of overhang angle.
"""
supportBlockRegions = supportGenerator.identifySupportRegions(
    myPart, OVERHANG_ANGLE, True
)

# Extract the solid support volumes
blockSupports = [block.supportVolume for block in supportBlockRegions]

"""
Generate the edges for visualisation
"""
edges = myPart.geometry.edges_unique
meshVerts = myPart.geometry.vertices
centroids = myPart.geometry.triangles_center

if True:
    """ Visualise Edges potentially requiring support"""
    edgeRays = np.vstack([meshVerts[edge] for edge in overhangEdges])
    visualize_support_edges = trimesh.load_path((edgeRays).reshape(-1, 2, 3))

    edge_supports = []
    for edge in overhangEdges:
        coords = np.vstack([meshVerts[edge, :]] * 2)
        coords[2:, 2] = 0.0

        extrudeFace = np.array([(0, 1, 3), (3, 2, 0)])
        edge_supports.append(trimesh.Trimesh(vertices=coords, faces=extrudeFace))

    """  Visualise Point Supports """

    point_supports = []
    cylinder_rad = 0.5  # mm
    rays = []
    for pnt in pointOverhangs:
        coords = np.zeros((2, 3))
        coords[:, :] = meshVerts[pnt]
        coords[1, 2] = 0.0

        point_supports += trimesh.creation.cylinder(radius=cylinder_rad, segment=coords)
        rays.append(coords)

    # Alternatively can be visualised by lines
    rays = np.hstack([meshVerts[pointOverhangs]] * 2).reshape(-1, 2, 3)
    rays[:, 1, 2] = 0.0
    visualize_support_pnts = trimesh.load_path(rays)

# Make the normal part transparent
myPart.geometry.visual.vertex_colors = [80, 80, 80, 125]

"""
Visualise all the support geometry
"""

""" Identify the sides of the block extrudes """
# s1 = trimesh.Scene([myPart.geometry] + blockSupports)
s1 = trimesh.Scene(blockSupports)

"""
The following section exports the group of support structures from the trimesh scene. 
"""

with open("overhangSupport.glb", "wb") as f:
    f.write(trimesh.exchange.gltf.export_glb(s1, include_normals=True))

with open("overhangSupport.stl", "wb") as f:
    f.write(trimesh.exchange.stl.export_stl(s1))

"""
Show only the volume block supports generated
"""
DISPLAY_BLOCK_VOLUME = True

if DISPLAY_BLOCK_VOLUME:
    s2 = trimesh.Scene([myPart.geometry, overhangMesh] + blockSupports)
    s2.show()

"""
The final section demonstrates slicing across the support structure previously generated.
Since we are using solid block supports, we slice them to get the boundary contours.
"""

# Slice at a specific Z height
z_height = 10.0

# Slice the support blocks
support_sections = []
for block in blockSupports:
    section = block.section(plane_origin=[0, 0, z_height], plane_normal=[0, 0, 1])
    if section is not None:
        support_sections.append(section)

# Also slice the part for context
part_section = myPart.geometry.section(
    plane_origin=[0, 0, z_height], plane_normal=[0, 0, 1]
)

# Visualize the sections
if support_sections:
    s3 = trimesh.Scene([part_section] + support_sections)
    print(f"Displaying cross-section at Z={z_height}")
    s3.show()

# Example of converting to PySLM Layer for hatching (if desired)
layer = Layer()
transformMat = np.eye(4)

for section in support_sections:
    # Convert to planar
    planarSection, transform = section.to_planar(transformMat)

    # Extract polygons from the planar section
    for poly in planarSection.polygons_full:
        # Convert shapely polygon to coordinates
        if poly.exterior:
            coords = np.array(poly.exterior.coords)
            layerGeom = ContourGeometry()
            layerGeom.coords = coords
            layer.geometry.append(layerGeom)

        for interior in poly.interiors:
            coords = np.array(interior.coords)
            layerGeom = ContourGeometry()
            layerGeom.coords = coords
            layer.geometry.append(layerGeom)

if len(layer.geometry) > 0:
    print("Plotting 2D layer of supports...")
    pyslm.visualise.plotSequential(layer, plotJumps=True, plotArrows=False)
