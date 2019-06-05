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

#ifndef __vtkGLTFExporter_h
#define __vtkGLTFExporter_h

#include "vtkSlicerOpenAnatomyExporterModuleLogicExport.h" // For export macro

#include "vtkExporter.h"

class VTK_SLICER_OPENANATOMYEXPORTER_MODULE_LOGIC_EXPORT vtkGLTFExporter : public vtkExporter
{
public:
  static vtkGLTFExporter *New();
  vtkTypeMacro(vtkGLTFExporter, vtkExporter);

  vtkSetStringMacro(FilePrefix);
  vtkGetStringMacro(FilePrefix);

protected:
  vtkGLTFExporter();
  ~vtkGLTFExporter() override;

  // Export all vtkActor in the scene that has vtkPolyData in it.
  void WriteData() override;

  char* FilePrefix;

  class vtkInternals;
  vtkInternals* Internals;
};

#endif
