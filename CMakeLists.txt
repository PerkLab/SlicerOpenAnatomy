cmake_minimum_required(VERSION 3.5)

project(SlicerOpenAnatomy)

#-----------------------------------------------------------------------------
# Extension meta-information
set(EXTENSION_HOMEPAGE "https://github.com/PerkLab/SlicerOpenAnatomy")
set(EXTENSION_CATEGORY "Segmentation")
set(EXTENSION_CONTRIBUTORS "Andras Lasso (PerkLab), Csaba Pinter (PerkLab), Michael Halle (SPL)")
set(EXTENSION_DESCRIPTION "3D Slicer extension for exporting Slicer scenes to use in the OpenAnatomy.org browser")
set(EXTENSION_ICONURL "https://raw.githubusercontent.com/PerkLab/SlicerOpenAnatomy/master/SlicerOpenAnatomy.png")
set(EXTENSION_SCREENSHOTURLS "https://raw.githubusercontent.com/PerkLab/SlicerOpenAnatomy/master/OpenAnatomyExport/img/Screenshot01.png https://raw.githubusercontent.com/PerkLab/SlicerOpenAnatomy/master/OpenAnatomyExport/img/Screenshot02.png https://raw.githubusercontent.com/PerkLab/SlicerOpenAnatomy/master/OpenAnatomyExport/img/Screenshot03.png")
set(EXTENSION_DEPENDS "NA") # Specified as a space separated string, a list or 'NA' if any

#-----------------------------------------------------------------------------
# Extension dependencies
find_package(Slicer REQUIRED)
include(${Slicer_USE_FILE})

#-----------------------------------------------------------------------------
# Extension modules
add_subdirectory(OpenAnatomyExport)
add_subdirectory(AtlasEditor)
## NEXT_MODULE

#-----------------------------------------------------------------------------
include(${Slicer_EXTENSION_GENERATE_CONFIG})
include(${Slicer_EXTENSION_CPACK})
