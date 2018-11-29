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
#define TINYGLTF_IMPLEMENTATION
#define STB_IMAGE_IMPLEMENTATION
#define STB_IMAGE_WRITE_IMPLEMENTATION

// OpenAnatomyExporter Logic includes
#include "vtkGLTFExporter.h"

using namespace tinygltf;

// MRML includes
#include <vtkMRMLScene.h>

// VTK includes TODO:
#include <vtkActorCollection.h>
#include <vtkAssemblyPath.h>
#include <vtkDataSet.h>
#include <vtkIntArray.h>
#include <vtkNew.h>
#include <vtkObjectFactory.h>
#include <vtkPolyData.h>
#include <vtkProperty.h>
#include <vtkRenderer.h>
#include <vtkRenderWindow.h>
#include <vtkTransform.h>

vtkStandardNewMacro(vtkGLTFExporter);

vtkGLTFExporter::vtkGLTFExporter()
{
  this->OutFileName = "defaultGLTF";
  this->Model.asset.version = "2.0";
  this->Model.asset.generator = "vtkGLTFExporter";

  // TEST CODE // !!!!!!!!!!!!
   
   tinygltf::TinyGLTF loader;
   std::string err;
   std::string warn;
   std::string input_filename;
   std::string output_filename;
   //for test code, have the absolute path the a gltf sample as the input_filename. 
   //gltf samples can be found: https://github.com/KhronosGroup/glTF-Sample-Models/tree/master/2.0
   output_filename = "c:\\users\\schoueib\\desktop\\seg.gltf";
   input_filename = "c:\\users\\schoueib\\desktop\\gltfexamples\\box.gltf";
   //warn: accessor array has hard coded indicies
  const tinygltf::Accessor& accessor = Model.accessors[Model.meshes[0].primitives[0].attributes["NORMALS"]];
  const tinygltf::BufferView& bufferView = Model.bufferViews[accessor.bufferView];
  const tinygltf::Buffer& buffer = Model.buffers[bufferView.buffer];
  const float* positions = reinterpret_cast<const float*>(&buffer.data[bufferView.byteOffset + accessor.byteOffset]);
  for (size_t i = 0; i < accessor.count; ++i) {
    std::cout << "(" << positions[i * 3 + 0] << ", "// x
      << positions[i * 3 + 1] << ", " // y
      << positions[i * 3 + 2] << ")" // z
      << "\n";
  }
  //given a populated model write the model to a gltf file. 
  loader.WriteGltfSceneToFile(&Model, output_filename, false,false,false,false);
  int i=0; ++i; // add break here
  //// TEST CODE // !!!!!!!!!!!!!!
}


vtkGLTFExporter::~vtkGLTFExporter()
{
  delete[] this->OutFileName; 
}

void vtkGLTFExporter::WriteData()
{
  //every vtk actor in the scene to be exported will be created and added to model.
  //model will then be written to a file using tinygltf::writegltfscenetofile(model,...) 

  vtkRenderer *ren = this->ActiveRenderer;
  if (!ren)
  {
    //TODO Debug: 
    //ren = this->RenderWindow->GetRenderers()->GetFirstRenderer();
  }

  if (ren->GetActors()->GetNumberOfItems() < 1)
  {
    vtkErrorMacro(<< "no actors found for writing .gltf file.");
    return;
  }
  //Create a list of actors in the scene to be accessed later
  vtkActorCollection *allActors = ren->GetActors();
  vtkCollectionSimpleIterator actorsIterator; 
  vtkActor *anActor;
  int idStart = 1;
  for (allActors->InitTraversal(actorsIterator); (anActor = allActors->GetNextActor(actorsIterator)); )
  {
    vtkAssemblyPath *aPath;
    for (anActor->InitPathTraversal(); (aPath = anActor->GetNextPath()); )
    {
      vtkActor *aPart = vtkActor::SafeDownCast(aPath->GetLastNode()->GetViewProp());
      this->WriteAnActor(aPart);
    }
  }
}

void vtkGLTFExporter::WriteAnActor(vtkActor *anActor)
{
  vtkDataSet *dataSet;
  vtkNew<vtkPolyData> polyData;
  vtkPointData *pntData;
  vtkPoints *points;
  vtkDataArray *tcoords;
  int i, i1, i2, idNext;
  vtkProperty *actorProp;
  double *tempd;
  double *p;
  vtkCellArray *cells;
  vtkNew<vtkTransform> trans;
  vtkIdType npts = 0;
  vtkIdType *indx = nullptr;

  //Filter the actor collection for actors that should be written
  if (anActor->GetMapper() == nullptr)
  {
    return;
  }

  if (anActor->GetVisibility() == 0)
  {
    return;
  }
  //TODO: Add filter for number of cells
}
