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
#include <vtkPolyDataMapper.h>
#include <vtkProperty.h>
#include <vtkRenderer.h>
#include <vtkRendererCollection.h>
#include <vtkRenderWindow.h>
#include <vtkTransform.h>
#include <vtkGeometryFilter.h>
#include "vtksys/SystemTools.hxx"
#include "vtk_jsoncpp.h"
#include "vtkCompositeDataIterator.h"
#include "vtkCompositeDataSet.h"

vtkStandardNewMacro(vtkGLTFExporter);
namespace {

  vtkPolyData *findPolyData(vtkDataObject* input)
  {
    // do we have polydata?
    vtkPolyData *pd = vtkPolyData::SafeDownCast(input);
    if (pd)
    {
      return pd;
    }
    vtkCompositeDataSet *cd = vtkCompositeDataSet::SafeDownCast(input);
    if (cd)
    {
      vtkSmartPointer<vtkCompositeDataIterator> iter;
      iter.TakeReference(cd->NewIterator());
      for (iter->InitTraversal(); !iter->IsDoneWithTraversal(); iter->GoToNextItem())
      {
        pd = vtkPolyData::SafeDownCast(iter->GetCurrentDataObject());
        if (pd)
        {
          return pd;
        }
      }
    }
    return nullptr;
  }
}
vtkGLTFExporter::vtkGLTFExporter()
{
  this->Model.asset.version = "2.0";
  this->Model.asset.generator = "vtkGLTFExporter";
  this->GltfFileName = "C:\\Users\\schoueib\\Desktop\\gltfExamples\\TESTGLTF"; 
  tinygltf::Buffer initBuffer = {};
  this->Model.buffers.push_back(initBuffer);
}


vtkGLTFExporter::~vtkGLTFExporter()
{
  delete[] this->GltfFileName; 
}

void vtkGLTFExporter::WriteData() //called by write()
{
  ///TODO: Add actor filter here
  //every vtk actor in the scene to be exported will be created and added to model.
  //model will then be written to a file using tinygltf::writegltfscenetofile(model,...) 

  vtkRenderer *ren = this->ActiveRenderer;
  if (!ren)
  {
    ren = this->RenderWindow->GetRenderers()->GetFirstRenderer();
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
  tinygltf::TinyGLTF loader;
  loader.WriteGltfSceneToFile(&Model, GltfFileName, false, false, false, false);
}

void vtkGLTFExporter::WriteAnActor(vtkActor *Actor)
{
  vtkDataSet *dataSet;
  vtkPolyData *polyData;
  vtkPointData *pntData;
  vtkPoints *points;
  vtkDataArray *tcoords;
  int i, i1, i2, idNext;
  vtkProperty *actorProp;
  double *tempd;
  double *pointsTriplet;
  vtkCellArray *cells;
  vtkNew<vtkTransform> trans;
  vtkIdType npts = 0;
  vtkIdType *indx = nullptr;

  //Filter the actor collection for actors that should be written
  ///TODO: debug actor filter 
  vtkPolyDataMapper* mapper = vtkPolyDataMapper::SafeDownCast(Actor->GetMapper()); //get the mapper for the actor
  vtkPolyData *pd = findPolyData(Actor->GetMapper()->GetInputDataObject(0, 0));
  if (!pd &&!pd->GetPolys() && !pd->GetNumberOfCells() > 0)
  {
    return;
  }

  // Write Poly Data
  // Create Buffer, BufferView, and Accessor with proper references. 
  //write point data

  polyData = mapper->GetInput();
  points = vtkPoints::New();
  points = polyData->GetPoints();
  double pt[3];
  float fpt[3];
  std::vector <unsigned char> dataArray = this->Model.buffers[0].data;
  //tinygltf::buffer has no member "bytelength" which is required in the gltf v2.0 specs. Must clarify. 
  int temp = this->Model.buffers[0].data.size();
  size_t prevBufferSize = static_cast<size_t>(temp);

  for (int i = 0 ; i<=points->GetNumberOfPoints(); i++)
  {
    points->GetPoint(i,pt);
    fpt[0] = pt[0];
    fpt[1] = pt[1];
    fpt[2] = pt[2];
    unsigned char a = reinterpret_cast<unsigned char>(fpt);
    dataArray.push_back(a);
  }

  this->Model.buffers[0].data = dataArray;
  int temp2 = this->Model.buffers[0].data.size();
  size_t newBufferSize = static_cast<size_t>(temp2);
  //populate bufferview
  tinygltf::BufferView bv = {};
  bv.buffer = 0;
  bv.byteOffset = prevBufferSize + 1;
  bv.byteLength = (newBufferSize - prevBufferSize);
  this->Model.bufferViews.push_back(bv);
  //populate Accessor
  tinygltf::Accessor   ac = {};
  ac.byteOffset = bv.byteOffset;
  ac.bufferView = this->Model.bufferViews.size() - 1;
  ac.componentType = 5126;  
  ac.count = points->GetNumberOfPoints();
  ac.type = TINYGLTF_TYPE_VEC3;
  this->Model.accessors.push_back(ac);


  ///TODO: write cell data

}