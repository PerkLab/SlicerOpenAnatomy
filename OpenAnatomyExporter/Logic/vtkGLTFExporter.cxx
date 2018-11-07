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
// OpenAnatomyExporter Logic includes
#include "vtkGLTFExporter.h"

// MRML includes
#include <vtkMRMLScene.h>

// VTK includes TODO:
#include <vtkIntArray.h>
#include <vtkNew.h>
#include <vtkObjectFactory.h>
#include <vtkActorCollection.h>
#include <vtkDataSet.h>
#include <vtkPolyData.h>
#include <vtkAssemblyPath.h>

vtkStandardNewMacro(vtkGLTFExporter);

vtkGLTFExporter::vtkGLTFExporter()
{
  this->FilePrefix = nullptr;
}

vtkGLTFExporter::~vtkGLTFExporter()
{
  delete[] this->FilePrefix;
  delete[] this->FileName; 
  delete[] this->GltfFileAsset;
}

void vtkGLTFExporter::WriteData()
{
  if (this->FilePrefix == nullptr)
  {
    vtkErrorMacro(<< "Please specify file prefix to use");
    return;
  }

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

  //try opening the file
  std::string gltfFilePath = std::string(this->FilePrefix) + ".gltf";
  FILE *fpGltf = fopen(gltfFilePath.c_str(), "w");
  if (!fpGltf)
  {
    vtkErrorMacro(<< "unable to open .gltf files ");
    return;
  }
  std::string binFilePath = std::string(this->FilePrefix) + ".bin";
  FILE *fpBin = fopen(binFilePath.c_str(), "w");
  if (!fpBin)
  {
    fclose(fpGltf);
    vtkErrorMacro(<< "unable to open .bin files ");
    return;
  }

  
  if (this->GetGltfFileAsset())
  {
    fprintf(fpGltf, "{ %s\n\t", this->GetGltfFileAsset());
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
      this->WriteAnActor(aPart, fpGltf, fpBin, idStart);
    }
  }

  fclose(fpGltf);
  fclose(fpBin);
}

void vtkGLTFExporter::WriteAnActor(vtkActor *anActor, FILE *fpGltf, FILE *fpBin, int &idStart)
{
  vtkDataSet *dataSet;
  vtkNew<vtkPolyData> polyData;
  vtkPointData *pntData;
  vtkPoints *points;
  vtkDataArray *tcoords;
  int i, i1, i2, idNext;
  vtkProperty *prop;
  double *tempd;
  double *p;
  vtkCellArray *cells;
  vtkNew<vtkTransform> trans;
  vtkIdType npts = 0;
  vtkIdType *indx = nullptr;
  
  if (anActor->GetMapper() == nullptr)
  {
    return;
  }
}

