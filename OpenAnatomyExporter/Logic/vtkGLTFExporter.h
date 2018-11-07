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

class vtkActor;

#ifndef __vtkGLTFExporter_h
#define __vtkGLTFExporter_h

// Slicer includes
#include "vtkSlicerModuleLogic.h"

// MRML includes

// STD includes
#include <cstdlib>
#include "vtkIOExportModule.h" // For export macro
#include "vtkSlicerOpenAnatomyExporterModuleLogicExport.h"
#include "vtkExporter.h"

class VTKIOEXPORT_EXPORT vtkGLTFExporter : public vtkExporter 
{
public:
  static vtkGLTFExporter *New();
  vtkTypeMacro(vtkGLTFExporter, vtkExporter);

  //@{
  /**
  * Specify the prefix of the files to write out. The resulting filenames
  * will have .gltf and .bin 
  */
  vtkSetStringMacro(FilePrefix);
  vtkGetStringMacro(FilePrefix);
  //@}
  vtkSetStringMacro(FileName);
  vtkGetStringMacro(FileName);

  //@}
  vtkSetStringMacro(GltfFileAsset);
  vtkGetStringMacro(GltfFileAsset);


protected:
  vtkGLTFExporter();
  ~vtkGLTFExporter() override;

  void WriteData() override;  
  void WriteAnActor(vtkActor *anActor, FILE fpGltf, FILE fpBin,int count );
  char *FileName; 
  char *FilePrefix;
  char *GltfFileAsset;
private:

  vtkGLTFExporter(const vtkGLTFExporter&) = delete;
  void operator=(const vtkGLTFExporter&) = delete;

};

#endif
