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

#include "ThirdParty/tiny_gltf.h"

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

#include <cstdlib>

vtkStandardNewMacro(vtkGLTFExporter);

//----------------------------------------------------------------------------
class vtkGLTFExporter::vtkInternals
{
public:
  static void AddActorToModel(tinygltf::Model& gltfModel, vtkActor* anActor, std::string namePrefix);
  static vtkPolyData* GetPolyData(vtkDataObject* input);
};

void AddVtkArrayToBuffer(tinygltf::Model& gltfModel, int bufferIndex, vtkDataArray* dataArray, size_t& offset, size_t& size)
{
  offset = gltfModel.buffers[0].data.size();
  size = dataArray->GetNumberOfTuples() * dataArray->GetNumberOfComponents() * dataArray->GetElementComponentSize();
  gltfModel.buffers[0].data.resize(offset + size);
  memcpy(&(gltfModel.buffers[0].data[offset]), dataArray->GetVoidPointer(0), size);
}

int GetGltfComponentTypeFromVtkDataType(int vtkDataType)
{
  switch (vtkDataType)
  {
  case VTK_CHAR: return TINYGLTF_COMPONENT_TYPE_BYTE;
  case VTK_SIGNED_CHAR: return TINYGLTF_COMPONENT_TYPE_BYTE;
  case VTK_UNSIGNED_CHAR: return TINYGLTF_COMPONENT_TYPE_UNSIGNED_BYTE;
  case VTK_SHORT: return TINYGLTF_COMPONENT_TYPE_SHORT;
  case VTK_UNSIGNED_SHORT: return TINYGLTF_COMPONENT_TYPE_UNSIGNED_SHORT;
  case VTK_INT: return TINYGLTF_COMPONENT_TYPE_INT;
  case VTK_UNSIGNED_INT: return TINYGLTF_COMPONENT_TYPE_UNSIGNED_INT;
  case VTK_FLOAT: return TINYGLTF_COMPONENT_TYPE_FLOAT;
  case VTK_DOUBLE: return TINYGLTF_COMPONENT_TYPE_DOUBLE;
  default:
    // unsupported data type
    return -1;
  }
}
//----------------------------------------------------------------------------
void vtkGLTFExporter::vtkInternals::AddActorToModel(tinygltf::Model& gltfModel, vtkActor* actor, std::string namePrefix)
{
  vtkPolyDataMapper* mapper = vtkPolyDataMapper::SafeDownCast(actor->GetMapper());
  vtkPolyData* polyData = vtkGLTFExporter::vtkInternals::GetPolyData(actor->GetMapper()->GetInputDataObject(0, 0));
  if (!polyData || !polyData->GetPolys() || !polyData->GetNumberOfCells())
  {
    return;
  }
  //vtkPolyData* polyData = mapper->GetInput();

  // Write Poly Data
  // Create Buffer, BufferView, and Accessor with proper references. 
  //write point data ============================================================================================
  //do not need to write a buffer as there is only one buffer to hold all actors' data 

  if (gltfModel.buffers.empty())
  {
    tinygltf::Buffer initBuffer = {};
    gltfModel.buffers.push_back(initBuffer); //one buffer to hold all data
  }
  
  const int bufferIndex = 0;

  vtkPoints* points = polyData->GetPoints();

  size_t offset = 0;
  size_t size = 0;
  AddVtkArrayToBuffer(gltfModel, bufferIndex, points->GetData(), offset, size);

  //write  bufferview
  tinygltf::BufferView bv = {};
  bv.name = namePrefix+"_positions_bv";
  bv.buffer = 0;
  bv.byteOffset = offset;
  bv.byteLength = size;
  bv.target = TINYGLTF_TARGET_ARRAY_BUFFER;
  gltfModel.bufferViews.push_back(bv);

  //write  Accessor 
  tinygltf::Accessor ac = {};
  ac.name = namePrefix + "_positions_ac";
  ac.byteOffset = bv.byteOffset;
  ac.bufferView = gltfModel.bufferViews.size() - 1;
  ac.componentType = GetGltfComponentTypeFromVtkDataType(points->GetDataType());
  ac.count = points->GetNumberOfPoints();
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
  gltfModel.accessors.push_back(ac);

  //write the primitive
  tinygltf::Primitive aPrimitive = {};
  aPrimitive.mode = TINYGLTF_MODE_TRIANGLES;
  aPrimitive.attributes.insert(std::make_pair("POSITION", gltfModel.accessors.size() - 1));

  //end write point data ===============================================================
  //Write Cell Data

  vtkCellArray * polygons = polyData->GetPolys();
  vtkIdType npts;
  vtkIdType * indx;
  //save them to buffer
  std::vector <unsigned char> cellDataArray;
  int cellTemp = gltfModel.buffers[0].data.size();
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

  gltfModel.buffers[0].data.insert(gltfModel.buffers[0].data.end(), cellDataArray.begin(), cellDataArray.end());
  int cellArrSize = cellDataArray.size();
  size_t cellNewBufferSize = gltfModel.buffers[0].data.size();

  //write  bufferview
  tinygltf::BufferView bv2 = {};
  bv2.buffer = 0;
  bv2.byteOffset = cellPrevBufferSize;
  bv2.byteLength = (cellNewBufferSize - cellPrevBufferSize);
  gltfModel.bufferViews.push_back(bv2);

  //write  Accessor 
  tinygltf::Accessor   ac2 = {};
  ac2.byteOffset = bv2.byteOffset;
  ac2.bufferView = gltfModel.bufferViews.size() - 1;
  ac2.componentType = 5125;
  ac2.count = polygons->GetNumberOfCells();
  ac2.type = TINYGLTF_TYPE_SCALAR;
  gltfModel.accessors.push_back(ac2);
  aPrimitive.indices = gltfModel.accessors.size() - 1;

  //write the mesh
  tinygltf::Mesh aMesh = {};
  std::vector<tinygltf::Primitive> meshPrimitives;
  meshPrimitives.push_back(aPrimitive);
  aMesh.primitives = meshPrimitives;
  tinygltf::Node aNode;
  gltfModel.meshes.push_back(aMesh);
  aNode.mesh = gltfModel.meshes.size() - 1;
  gltfModel.nodes.push_back(aNode);
  gltfModel.scenes[0].nodes.push_back(gltfModel.nodes.size() - 1);
}

//----------------------------------------------------------------------------
vtkGLTFExporter::vtkGLTFExporter()
: Internals(new vtkGLTFExporter::vtkInternals())
{
  this->FilePrefix = nullptr;
}

//----------------------------------------------------------------------------
vtkGLTFExporter::~vtkGLTFExporter()
{
  this->SetFilePrefix(nullptr);
  delete this->Internals;
  this->Internals = nullptr;
}

//----------------------------------------------------------------------------
vtkPolyData* vtkGLTFExporter::vtkInternals::GetPolyData(vtkDataObject* input)
{
  // do we have polydata?
  vtkPolyData* pd = vtkPolyData::SafeDownCast(input);
  if (pd)
  {
    return pd;
  }
  vtkCompositeDataSet* cd = vtkCompositeDataSet::SafeDownCast(input);
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

//----------------------------------------------------------------------------
void vtkGLTFExporter::WriteData() //called by write()
{
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

  tinygltf::Model gltfModel;
  gltfModel.asset.version = "2.0";
  gltfModel.asset.generator = "vtkGLTFExporter";
  tinygltf::Scene initScene = {};
  gltfModel.scenes.push_back(initScene);
  gltfModel.defaultScene = 0;// an index to what node shall be rendered runtime 
  
  vtkPropCollection* pc = ren->GetViewProps();
  vtkProp* aProp = nullptr;
  vtkCollectionSimpleIterator pit;
  for (pc->InitTraversal(pit); (aProp = pc->GetNextProp(pit)); )
  {
    if (!aProp->GetVisibility())
    {
      continue;
    }
    vtkNew<vtkActorCollection> ac;
    aProp->GetActors(ac);
    vtkActor *anActor = nullptr;
    vtkCollectionSimpleIterator ait;
    for (ac->InitTraversal(ait); (anActor = ac->GetNextActor(ait)); )
    {
      vtkAssemblyPath *apath = nullptr;
      for (anActor->InitPathTraversal(); (apath = anActor->GetNextPath()); )
      {
        vtkActor* aPart = static_cast<vtkActor *>(apath->GetLastNode()->GetViewProp());
        if (aPart->GetVisibility() && aPart->GetMapper() && aPart->GetMapper()->GetInputAlgorithm())
        {
          aPart->GetMapper()->GetInputAlgorithm()->Update();
          vtkPolyData *pd = vtkGLTFExporter::vtkInternals::GetPolyData(aPart->GetMapper()->GetInputDataObject(0, 0));
          if (pd && pd->GetPolys() && pd->GetNumberOfCells() > 0)
          {
            vtkGLTFExporter::vtkInternals::AddActorToModel(gltfModel, aPart, "actor");
          }
        }
      }
    }
  }

  std::string gltfFileName = this->FilePrefix + std::string(".gltf");

  tinygltf::TinyGLTF gltfWriter;
  gltfWriter.WriteGltfSceneToFile(&gltfModel, gltfFileName, false, false, false, false);
}
