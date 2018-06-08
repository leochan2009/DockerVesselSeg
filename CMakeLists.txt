cmake_minimum_required(VERSION 3.5)

project(DockerVesselSeg)

#-----------------------------------------------------------------------------
# Extension meta-information
set(EXTENSION_HOMEPAGE "http://slicer.org/slicerWiki/index.php/Documentation/Nightly/Extensions/DockerVesselSeg")
set(EXTENSION_CATEGORY "Examples")
set(EXTENSION_CONTRIBUTORS "Longquan Chen (NCIGT), Junichi Tokuda (NCIGT)")
set(EXTENSION_DESCRIPTION "Module for vessel segmentation using deep learning via docker")
set(EXTENSION_ICONURL "http://www.example.com/Slicer/Extensions/DockerVesselSeg.png")
set(EXTENSION_SCREENSHOTURLS "http://www.example.com/Slicer/Extensions/DockerVesselSeg/Screenshots/1.png")
set(EXTENSION_DEPENDS "NA") # Specified as a space separated string, a list or 'NA' if any

#-----------------------------------------------------------------------------
# Extension dependencies
find_package(Slicer REQUIRED)
include(${Slicer_USE_FILE})

#-----------------------------------------------------------------------------
# Extension modules
add_subdirectory(DockerVesselSeg)
## NEXT_MODULE

#-----------------------------------------------------------------------------
include(${Slicer_EXTENSION_GENERATE_CONFIG})
include(${Slicer_EXTENSION_CPACK})
