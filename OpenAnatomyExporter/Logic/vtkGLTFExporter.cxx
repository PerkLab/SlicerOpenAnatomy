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
  this->GltfFileName = "C:\\Users\\schoueib\\Desktop\\gltfExamples\\newgltf.gltf"; 
  tinygltf::Buffer initBuffer = {};
  this->Model.buffers.push_back(initBuffer); //one buffer to hold all data 
  tinygltf::Scene initScene = {};
  this->Model.scenes.push_back(initScene); 
  this->Model.defaultScene = 0;// an index to what node shall be rendered runtime 

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
  vtkPropCollection *pc;
  vtkProp *aProp;
  pc = ren->GetViewProps();
  vtkCollectionSimpleIterator pit;
  for (pc->InitTraversal(pit); (aProp = pc->GetNextProp(pit)); )
  {
    if (!aProp->GetVisibility())
    {
      continue;
    }
    vtkNew<vtkActorCollection> ac;
    aProp->GetActors(ac);
    vtkActor *anActor;
    vtkCollectionSimpleIterator ait;
    for (ac->InitTraversal(ait); (anActor = ac->GetNextActor(ait)); )
    {
      vtkAssemblyPath *apath;
      vtkActor *aPart;
      for (anActor->InitPathTraversal(); (apath = anActor->GetNextPath()); )
      {
        aPart = static_cast<vtkActor *>(apath->GetLastNode()->GetViewProp());
        if (aPart->GetVisibility() && aPart->GetMapper() && aPart->GetMapper()->GetInputAlgorithm())
        {
          aPart->GetMapper()->GetInputAlgorithm()->Update();
          vtkPolyData *pd = findPolyData(aPart->GetMapper()->GetInputDataObject(0, 0));
          bool follower = aPart->IsA("vtkFollower");
          bool visible = aPart->GetVisibility();

          std::cout << "Is Visible? " << visible << endl;
          std::cout << "Is follower? " << follower << endl;
          if (pd &&pd->GetPolys() && pd->GetNumberOfCells() > 0 && follower == 0)
          {
            WriteAnActor(aPart);
          }
        }
      }
    }
  }
  tinygltf::TinyGLTF loader;
  loader.WriteGltfSceneToFile(&Model, GltfFileName, false, false, false, false);
}

void vtkGLTFExporter::WriteAnActor(vtkActor *Actor)
{
  //Filter the actor collection for actors that should be written
  ///TODO: debug actor filter 
  vtkPolyDataMapper* mapper = vtkPolyDataMapper::SafeDownCast(Actor->GetMapper()); //get the mapper for the actor
  vtkPolyData *pd = findPolyData(Actor->GetMapper()->GetInputDataObject(0, 0));
  if (!pd && !pd->GetPolys() && !pd->GetNumberOfCells() > 0)
  {
    return;
  }
  
  // Write Poly Data
  // Create Buffer, BufferView, and Accessor with proper references. 
  //write point data ============================================================================================
  //do not need to write a buffer as there is only one buffer to hold all actors' data 
  vtkPolyData *polyData;
  polyData = mapper->GetInput();
  vtkPoints *points;
  points = vtkPoints::New();
  points = polyData->GetPoints();
  double pt[3];
  float fpt[3];
  std::vector <unsigned char> pointDataArray = this->Model.buffers[0].data;
  //tinygltf::buffer has no member "bytelength" which is required in the gltf v2.0 specs. Must clarify. 
  int temp = this->Model.buffers[0].data.size();
  size_t prevBufferSize = static_cast<size_t>(temp);
  std::cout << "Numb Points: " << points->GetNumberOfPoints() << std::endl; 
  for (int i = 0; i < points->GetNumberOfPoints(); i++)
  {
    points->GetPoint(i, pt);
    fpt[0] = pt[0];
    fpt[1] = pt[1];
    fpt[2] = pt[2];
    std::vector<float> floatVector;
    floatVector.push_back(fpt[0]);
    floatVector.push_back(fpt[1]);
    floatVector.push_back(fpt[2]);
    const unsigned char* bytes = reinterpret_cast<const unsigned char*>(&floatVector[0]);
    std::vector<unsigned char> byteVec(bytes, bytes + sizeof(float) * floatVector.size());
    pointDataArray.insert(pointDataArray.end(), byteVec.begin(), byteVec.end());
  }
  this->Model.buffers[0].data.insert(this->Model.buffers[0].data.end(), pointDataArray.begin(), pointDataArray.end());
  int temp2 = this->Model.buffers[0].data.size();
  size_t newBufferSize = static_cast<size_t>(temp2);

  
  //write  bufferview
  tinygltf::BufferView bv = {};
  bv.buffer = 0;
  bv.byteOffset = prevBufferSize;
  bv.byteLength = (newBufferSize - prevBufferSize);
  this->Model.bufferViews.push_back(bv);
  
  //write  Accessor 
  tinygltf::Accessor   ac = {};
  ac.byteOffset = bv.byteOffset;
  ac.bufferView = this->Model.bufferViews.size() - 1;
  ac.componentType = 5126;
  ac.count = points->GetNumberOfPoints()*3;
  ac.type = TINYGLTF_TYPE_VEC3;
  //get bounds 
  double range[6];
  std::vector<double> minVal;
  std::vector<double> maxVal;
  points->GetBounds(range);
  //minimum Values
  minVal.push_back(range[0]);
  minVal.push_back(range[2]);
  minVal.push_back(range[4]);
  //max Values
  maxVal.push_back(range[1]);
  maxVal.push_back(range[3]);
  maxVal.push_back(range[5]);

  ac.minValues = minVal;
  ac.maxValues = maxVal;
  //write accessor to model
  this->Model.accessors.push_back(ac);

  //write the primitive
  tinygltf::Primitive aPrimitive = {};
  aPrimitive.mode = TINYGLTF_MODE_TRIANGLES;
  aPrimitive.attributes.insert(std::make_pair("POSITION", this->Model.accessors.size() - 1));

  


  //end write point data ===============================================================
  //Write Cell Data

  vtkCellArray *polygons = polyData->GetPolys();
  vtkIdType npts;
  vtkIdType *indx;
  //save them to buffer
  std::vector <unsigned char> cellDataArray = this->Model.buffers[0].data;

  int cellTemp = this->Model.buffers[0].data.size();
  size_t cellPrevBufferSize = static_cast<size_t>(cellTemp);
  for (polygons->InitTraversal(); polygons->GetNextCell(npts, indx); )
  {
    for (int j = 0; j < npts; ++j)
    {
      unsigned int value = static_cast<unsigned int>(indx[j]);
      int intValue = static_cast<int>(value);
      cellDataArray.push_back(intValue >> 24);
      cellDataArray.push_back(intValue >> 16);
      cellDataArray.push_back(intValue >> 8);
      cellDataArray.push_back(intValue);
    }  
  }
  this->Model.buffers[0].data.insert(this->Model.buffers[0].data.end(), cellDataArray.begin(), cellDataArray.end());
  int cellArrSize = cellDataArray.size();
  size_t cellNewBufferSize = static_cast<size_t>(cellArrSize);

  //write  bufferview
  tinygltf::BufferView bv2 = {};
  bv2.buffer = 0;
  bv2.byteOffset = cellPrevBufferSize;
  bv2.byteLength = (cellNewBufferSize - cellPrevBufferSize);
  this->Model.bufferViews.push_back(bv2);

  //write  Accessor 
  tinygltf::Accessor   ac2 = {};
  ac2.byteOffset = bv2.byteOffset;
  ac2.bufferView = this->Model.bufferViews.size() - 1;
  ac2.componentType = 5125;
  ac2.count = polygons->GetNumberOfCells();
  ac2.type = TINYGLTF_TYPE_SCALAR;
  this->Model.accessors.push_back(ac2);
  aPrimitive.indices = this->Model.accessors.size() - 1;

  //write the mesh
  tinygltf::Mesh aMesh = {};
  std::vector<tinygltf::Primitive> meshPrimitives;
  meshPrimitives.push_back(aPrimitive);
  aMesh.primitives = meshPrimitives;
  tinygltf::Node aNode;
  this->Model.meshes.push_back(aMesh);
  aNode.mesh = this->Model.meshes.size()-1;
  this->Model.nodes.push_back(aNode);
  this->Model.scenes[0].nodes.push_back(this->Model.nodes.size()-1);
}