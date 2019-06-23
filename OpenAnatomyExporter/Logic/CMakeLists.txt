project(vtkSlicer${MODULE_NAME}ModuleLogic)

set(KIT ${PROJECT_NAME})

set(${KIT}_EXPORT_DIRECTIVE "VTK_SLICER_${MODULE_NAME_UPPER}_MODULE_LOGIC_EXPORT")

set(${KIT}_INCLUDE_DIRECTORIES
  )

set(${KIT}_SRCS
  vtkSlicer${MODULE_NAME}Logic.cxx
  vtkSlicer${MODULE_NAME}Logic.h
  vtkGLTFDocumentLoader.cxx
  #vtkGLTFDocumentLoader.h
  vtkGLTFDocumentLoaderInternals.cxx
  #vtkGLTFDocumentLoaderInternals.h
  vtkGLTFExporter.cxx
  vtkGLTFExporter.h
  vtkGLTFImporter.cxx
  vtkGLTFImporter.h
  vtkGLTFReader.cxx
  vtkGLTFReader.h
  vtkGLTFUtils.cxx
  vtkGLTFUtils.h 
  )

set_source_files_properties(
  vtkGLTFDocumentLoaderInternals.cxx
  vtkGLTFDocumentLoader.cxx
  WRAP_EXCLUDE
  )

set(${KIT}_TARGET_LIBRARIES
  ${ITK_LIBRARIES}
  )

#-----------------------------------------------------------------------------
SlicerMacroBuildModuleLogic(
  NAME ${KIT}
  EXPORT_DIRECTIVE ${${KIT}_EXPORT_DIRECTIVE}
  INCLUDE_DIRECTORIES ${${KIT}_INCLUDE_DIRECTORIES}
  SRCS ${${KIT}_SRCS}
  TARGET_LIBRARIES ${${KIT}_TARGET_LIBRARIES}
  )

if(BUILD_TESTING)
  add_subdirectory(Testing)
endif()
