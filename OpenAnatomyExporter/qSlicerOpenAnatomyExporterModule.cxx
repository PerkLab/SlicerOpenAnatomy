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
#include <vtkSlicerOpenAnatomyExporterLogic.h>

// OpenAnatomyExporter includes
#include "qSlicerOpenAnatomyExporterModule.h"
#include "qSlicerOpenAnatomyExporterModuleWidget.h"

//-----------------------------------------------------------------------------
#if (QT_VERSION < QT_VERSION_CHECK(5, 0, 0))
#include <QtPlugin>
Q_EXPORT_PLUGIN2(qSlicerOpenAnatomyExporterModule, qSlicerOpenAnatomyExporterModule);
#endif

//-----------------------------------------------------------------------------
/// \ingroup Slicer_QtModules_ExtensionTemplate
class qSlicerOpenAnatomyExporterModulePrivate
{
public:
  qSlicerOpenAnatomyExporterModulePrivate();
};

//-----------------------------------------------------------------------------
// qSlicerOpenAnatomyExporterModulePrivate methods

//-----------------------------------------------------------------------------
qSlicerOpenAnatomyExporterModulePrivate::qSlicerOpenAnatomyExporterModulePrivate()
{
}

//-----------------------------------------------------------------------------
// qSlicerOpenAnatomyExporterModule methods

//-----------------------------------------------------------------------------
qSlicerOpenAnatomyExporterModule::qSlicerOpenAnatomyExporterModule(QObject* _parent)
  : Superclass(_parent)
  , d_ptr(new qSlicerOpenAnatomyExporterModulePrivate)
{
}

//-----------------------------------------------------------------------------
qSlicerOpenAnatomyExporterModule::~qSlicerOpenAnatomyExporterModule()
{
}

//-----------------------------------------------------------------------------
QString qSlicerOpenAnatomyExporterModule::helpText() const
{
  return "This is a loadable module that can be bundled in an extension";
}

//-----------------------------------------------------------------------------
QString qSlicerOpenAnatomyExporterModule::acknowledgementText() const
{
  return "This work was partially funded by NIH grant NXNNXXNNNNNN-NNXN";
}

//-----------------------------------------------------------------------------
QStringList qSlicerOpenAnatomyExporterModule::contributors() const
{
  QStringList moduleContributors;
  moduleContributors << QString("John Doe (AnyWare Corp.)");
  return moduleContributors;
}

//-----------------------------------------------------------------------------
QIcon qSlicerOpenAnatomyExporterModule::icon() const
{
  return QIcon(":/Icons/OpenAnatomyExporter.png");
}

//-----------------------------------------------------------------------------
QStringList qSlicerOpenAnatomyExporterModule::categories() const
{
  return QStringList() << "Examples";
}

//-----------------------------------------------------------------------------
QStringList qSlicerOpenAnatomyExporterModule::dependencies() const
{
  return QStringList();
}

//-----------------------------------------------------------------------------
void qSlicerOpenAnatomyExporterModule::setup()
{
  this->Superclass::setup();
}

//-----------------------------------------------------------------------------
qSlicerAbstractModuleRepresentation* qSlicerOpenAnatomyExporterModule
::createWidgetRepresentation()
{
  return new qSlicerOpenAnatomyExporterModuleWidget;
}

//-----------------------------------------------------------------------------
vtkMRMLAbstractLogic* qSlicerOpenAnatomyExporterModule::createLogic()
{
  return vtkSlicerOpenAnatomyExporterLogic::New();
}
