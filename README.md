# PySLM Python Library for Selective Laser Melting and Additive Manufacturing

![PySLM - Library for Additive Manufacturing and 3D Printing including Selective Laser Melting](https://github.com/xiechao06/pyslm/raw/master/docs/images/pyslm.png)

[![Python Package](https://github.com/xiechao06/pyslm/actions/workflows/pythonpublish.yml/badge.svg)](https://github.com/xiechao06/pyslm/actions)
[![Documentation Status](https://readthedocs.org/projects/pyslm/badge/?version=latest)](https://pyslm.readthedocs.io/en/latest/?badge=latest)
[![PyPI version](https://badge.fury.io/py/PythonSLM.svg)](https://badge.fury.io/py/PythonSLM)
[![Downloads](https://static.pepy.tech/personalized-badge/pythonslm?period=total&units=international_system&left_color=black&right_color=orange&left_text=Downloads)](https://pepy.tech/project/pythonslm)

PySLM is a Python library for supporting development and generation of build files in Additive Manufacturing or 3D
Printing, in particular Selective Laser Melting (SLM), Direct Metal Laser Sintering (DMLS) platforms typically used
in both academia and industry. The core capabilities aim to include slicing, hatching and support generation and
providing an interface to the binary build file formats available for platforms. The library is built of core classes
which may provide the basic functionality to generate the scan vectors used on systems and also be used as building
blocks to prototype and develop new algorithms.

This library provides design tools for use in Additive Manufacturing including the slicing, hatching, support generation
and related analysis tools (e.g. overhang analysis, build-time estimation).

PySLM is built-upon [Trimesh](https://github.com/mikedh/trimesh) v4.0 for mesh handling and manipulation
and the polygon clipping and offsetting provided by [Clipper 2](https://github.com/AngusJohnson/Clipper2) library
via [Pyclipr](https://github.com/drlukeparry/pyclipr), which together leveraged to provide the slicing and
manipulation of polygons, such as offsetting and clipping of scan vectors used.

The aims of this library is to provide a useful set of tools for prototyping novel pre-processing approaches to aid
research and development of Additive Manufacturing processes, amongst an academic environment. The tools aim to
compliment experimental and analytical studies that can enrich scientific understanding of the process. This includes
data-fusion from experiments and sensors within the process but also enhancing the capability of the process by
providing greater control over the process. Furthermore, the open nature of the library intends to inform and educate
those interested in the underlying algorithms of preparing toolpaths in Additive Manufacturing.

## Current Features

PySLM is building up a core feature set aiming to provide the basic blocks for primarily generating the scan paths and
additional design features used for AM and 3D printing systems typically (SLM/SLS/SLA) systems which consolidate material
using a single/multi point exposure by generating a series of scan vectors in a region.

### Slicing

* Slicing of triangular meshes supported via the [Trimesh](https://github.com/mikedh/trimesh) library.
* Simplification of 2D layer boundaries
* Bitmap slicing for SLA, DLP, Inkjet Systems

### Hatching

The following operations are provided as a convenience to aid the development of novel scan strategies in Selective
Laser Melting:

* Offsetting of contours and boundaries
* Trimming of lines and hatch vectors (sequentially ordered and sorted)

The following scan strategies have been implemented as reference for AM platforms:

* Standard 'alternating' hatching
* Stripe scan strategy
* Island or checkerboard scan strategy

### Support Structure Generation

PySLM provides underlying tools and a framework for identifying and generating support structures suitable for SLM
and other AM processes. Tools are provided identifying overhang areas based on their mesh and connectivity
information, but also using a projection based method. The projection method takes advantage of GPU GLSL shaders for
providing an efficient raytracing approach. Using the [Manifold](https://github.com/elalish/manifold) boolean CSG
library, an algorithm for extracting precise definition of volumetric support regions. These regions are segmented
based on self-intersections with the mesh. From these volumes, porous grid-truss structure suitable for SLM based
process can be generated.

<div align="center">
<img src="https://github.com/xiechao06/pyslm/raw/master/docs/images/pyslmSupportStructures.png" alt="The tools available in PySLM for locating overhang regions and support regions for 3D Printing and generating volumetric block supports alongside grid-truss based support structures suitable for SLM." width="80%">
</div>

* Extracting overhang surfaces from meshes with optional connectivity information
* Projection based block and truss support structure generation
  * 3D intersected support volumes are generated from overhang regions using OpenGL ray-tracing approach
  * Generate a truss grid using support volumes suitable for Metal AM processes
  * Perforated teeth for support connection
  * Exact support volume generation using [Manifold](https://github.com/elalish/manifold) CSG library

### Visualisation

The laser scan vectors can be visualised using `Matplotlib`. The order of the scan vectors can be shown to aid
development of the scan strategies, but additional information such length, laser parameter information associated
with each scan vector can be shown.

<div align="center">
<img src="https://github.com/xiechao06/pyslm/raw/master/docs/images/pyslmVisualisationTools.png" alt="The tools available in PySLM for visualising analyisng collections of scan vectors used in SLM." width="80%">
</div>

* Scan vector plots (including underlying BuildStyle information and properties)
* Exposure point visualisation
* Exposure (effective heat) map generation
* Overhang visualisation

### Analysis

* Build time estimation tools
  * Based on scan strategy and geometry
  * Time estimation based on LayerGeometry
* Iterators (Scan Vector and Exposure Points) useful for simulation studies

### Export to Machine Files

Currently the capability to enable translation to commercial machine build platforms is being providing through a
supporting library called [libSLM](https://github.com/drlukeparry/libSLM). This is a c++ library to enable efficient
import and export across various commercial machine build files. With support from individuals the following machine
build file formats have been developed.

* Renishaw MTT (**.mtt**),
* DMG Mori Realizer (**.rea**),
* CLI/CLI+ & .ilt (**.cli**/.**.ilt**),
* EOS SLI formats (**.sli**)
* SLM Solutions (**.slm**).

If you would like to support implementing a custom format, please raise a [request](https://github.com/xiechao06/pyslm/issues).
For further information, see the latest [release notes](https://github.com/xiechao06/pyslm/blob/dev/CHANGELOG.md).

## Installation

Installation is currently supported on Windows, Mac OS X and Linux environments.
The pre-requisites for using PySLM can be installed via [uv](https://docs.astral.sh/uv/#installation).

```bash
uv sync
uv pip install -e .
```

## Usage

A basic example below, shows how relatively straightforward it is to generate a single layer from a STL mesh which
generates a the hatch infill using a Stripe Scan Strategy typically employed on some commercial systems to limit the
maximum scan vector length generated in a region.

```python
import pyslm
import pyslm.visualise
from pyslm import hatching as hatching

# Imports the part and sets the geometry to an STL file (frameGuide.stl)
solidPart = pyslm.Part('myFrameGuide')
solidPart.setGeometry('../models/frameGuide.stl')

# Set te slice layer position
z = 23.

# Create a StripeHatcher object for performing any hatching operations
myHatcher = hatching.StripeHatcher()
myHatcher.stripeWidth = 5.0 # [mm]

# Set the base hatching parameters which are generated within Hatcher
myHatcher.hatchAngle = 10 # [°]
myHatcher.volumeOffsetHatch = 0.08 # [mm]
myHatcher.spotCompensation = 0.06 # [mm]
myHatcher.numInnerContours = 2
myHatcher.numOuterContours = 1

# Slice the object at Z and get the boundaries
geomSlice = solidPart.getVectorSlice(z)

# Perform the hatching operations
layer = myHatcher.hatch(geomSlice)

# Plot the layer geometries generated
pyslm.visualise.plot(layer, plot3D=False, plotOrderLine=True) # plotArrows=True)
```

The result of the script output is shown here

<div align="center">
<img src="https://github.com/xiechao06/pyslm/raw/master/docs/images/stripe_scan_strategy_example.png" alt="PySLM - Illustration of a Stripe Scan Strategy employed in 3D printing" width="50%">
</div>

For further guidance please look at documented examples are provided in
[examples](https://github.com/xiechao06/pyslm/tree/master/examples).
