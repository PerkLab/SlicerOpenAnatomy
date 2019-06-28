/*==============================================================================

  Program: 3D Slicer

  Portions (c) Copyright Brigham and Women's Hospital (BWH) All Rights Reserved.

  See COPYRIGHT.txt
  or http://www.slicer.org/copyright/copyright.txt for details.

  Unless required by applicable law or agreed to in writing, software
  distributed under the License is distributed on an "AS IS" BASIS,
  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
  See the License for the specific language governing permissions and
  limitations under the License.

==============================================================================*/

// MRMLLogic includes
#include "vtkGLTFExporter.h"

// MRML includes
#include "vtkMRMLCoreTestingMacros.h"

// VTK includes
#include <vtkActor.h>
#include <vtkPolyDataMapper.h>
#include <vtkRenderer.h>
#include <vtkRenderWindow.h>
#include <vtkSphereSource.h>
#include <vtkTesting.h>

// STD includes

#include "vtkMRMLCoreTestingMacros.h"

using namespace vtkAddonTestingUtilities;
using namespace vtkMRMLCoreTestingUtilities;

//----------------------------------------------------------------------------
size_t fileSize(const std::string& filename)
{
  size_t size = 0;
  FILE* f = fopen(filename.c_str(), "r");
  if (f)
  {
    fseek(f, 0, SEEK_END);
    size = ftell(f);
    fclose(f);
  }
  else
  {
    std::cerr << "Error: cannot open file " << filename << std::endl;
  }

  return size;
}

//----------------------------------------------------------------------------
int vtkGLTFExporterTest1(int argc, char * argv[])
{
  vtkNew<vtkTesting> testHelper;
  testHelper->AddArguments(argc, const_cast<const char**>(argv));
  vtkStdString outputDirectory = testHelper->GetTempDirectory();

  std::string filenamePrefix = outputDirectory + std::string("/") + std::string("vtkGLTFExporterTest1");

  vtkNew<vtkSphereSource> sphere;
  vtkNew<vtkPolyDataMapper> mapper;
  mapper->SetInputConnection(sphere->GetOutputPort());
  vtkNew<vtkActor> actor;
  actor->SetMapper(mapper);
  vtkNew<vtkRenderer> renderer;
  renderer->AddActor(actor);
  vtkNew<vtkRenderWindow> window;
  window->AddRenderer(renderer);

  vtkNew<vtkGLTFExporter> exporter;
  exporter->SetRenderWindow(window);
  exporter->SetFileName(filenamePrefix.c_str());
  exporter->Write();

  std::string filename = filenamePrefix += ".gltf";

  size_t correctSize = fileSize(filename);
  if (correctSize == 0)
  {
    return EXIT_FAILURE;
  }

  actor->VisibilityOff();
  exporter->Write();
  size_t noDataSize = fileSize(filename);
  if (noDataSize == 0)
  {
    return EXIT_FAILURE;
  }

  if (noDataSize >= correctSize)
  {
    std::cerr << "Error: file should contain data for a visible actor"
      "and not for a hidden one." << std::endl;
    return EXIT_FAILURE;
  }

  actor->VisibilityOn();
  actor->SetMapper(nullptr);
  exporter->Write();
  size_t size = fileSize(filename);
  if (size == 0)
  {
    return EXIT_FAILURE;
  }
  if (size > noDataSize)
  {
    std::cerr << "Error: file should not contain geometry"
      " (actor has no mapper)" << std::endl;
    return EXIT_FAILURE;
  }

  actor->SetMapper(mapper);
  mapper->RemoveAllInputConnections(0);
  exporter->Write();
  size = fileSize(filename);
  if (size == 0)
  {
    return EXIT_FAILURE;
  }
  if (size > noDataSize)
  {
    std::cerr << "Error: file should not contain geometry"
      " (mapper has no input)" << std::endl;
    return EXIT_FAILURE;
  }

  return EXIT_SUCCESS;
}
