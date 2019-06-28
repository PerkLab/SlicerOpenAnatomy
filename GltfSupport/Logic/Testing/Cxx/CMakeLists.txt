set(KIT ${PROJECT_NAME})

set(TEMP "${Slicer_BINARY_DIR}/Testing/Temporary")

#-----------------------------------------------------------------------------
set(KIT_TEST_SRCS
  vtkGLTFExporterTest1.cxx
  )

#-----------------------------------------------------------------------------
slicerMacroConfigureModuleCxxTestDriver(
  NAME ${KIT}
  SOURCES ${KIT_TEST_SRCS}
  WITH_VTK_DEBUG_LEAKS_CHECK
  WITH_VTK_ERROR_OUTPUT_CHECK
  )

#-----------------------------------------------------------------------------
simple_test(vtkGLTFExporterTest1 -T ${TEMP})
