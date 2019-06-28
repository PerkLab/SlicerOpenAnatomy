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

// GltfSupport Logic includes
#include <vtkSlicerGltfSupportLogic.h>

// GltfSupport includes
#include "qSlicerGltfSupportModule.h"
#include "qSlicerGltfSupportModuleWidget.h"

//-----------------------------------------------------------------------------
#if (QT_VERSION < QT_VERSION_CHECK(5, 0, 0))
#include <QtPlugin>
Q_EXPORT_PLUGIN2(qSlicerGltfSupportModule, qSlicerGltfSupportModule);
#endif

//-----------------------------------------------------------------------------
/// \ingroup Slicer_QtModules_ExtensionTemplate
class qSlicerGltfSupportModulePrivate
{
public:
  qSlicerGltfSupportModulePrivate();
};

//-----------------------------------------------------------------------------
// qSlicerGltfSupportModulePrivate methods

//-----------------------------------------------------------------------------
qSlicerGltfSupportModulePrivate::qSlicerGltfSupportModulePrivate()
{
}

//-----------------------------------------------------------------------------
// qSlicerGltfSupportModule methods

//-----------------------------------------------------------------------------
qSlicerGltfSupportModule::qSlicerGltfSupportModule(QObject* _parent)
  : Superclass(_parent)
  , d_ptr(new qSlicerGltfSupportModulePrivate)
{
}

//-----------------------------------------------------------------------------
qSlicerGltfSupportModule::~qSlicerGltfSupportModule()
{
}

//-----------------------------------------------------------------------------
QString qSlicerGltfSupportModule::helpText() const
{
  return "This is a loadable module that can be bundled in an extension";
}

//-----------------------------------------------------------------------------
QString qSlicerGltfSupportModule::acknowledgementText() const
{
  return "This work was partially funded by NIH grant NXNNXXNNNNNN-NNXN";
}

//-----------------------------------------------------------------------------
QStringList qSlicerGltfSupportModule::contributors() const
{
  QStringList moduleContributors;
  moduleContributors << QString("John Doe (AnyWare Corp.)");
  return moduleContributors;
}

//-----------------------------------------------------------------------------
QIcon qSlicerGltfSupportModule::icon() const
{
  return QIcon(":/Icons/GltfSupport.png");
}

//-----------------------------------------------------------------------------
QStringList qSlicerGltfSupportModule::categories() const
{
  return QStringList() << "OpenAnatomy";
}

//-----------------------------------------------------------------------------
QStringList qSlicerGltfSupportModule::dependencies() const
{
  return QStringList();
}

//-----------------------------------------------------------------------------
bool qSlicerGltfSupportModule::isHidden() const
{
  // infrastructure module only, there is no GUI
  return true;
}

//-----------------------------------------------------------------------------
void qSlicerGltfSupportModule::setup()
{
  this->Superclass::setup();
}

//-----------------------------------------------------------------------------
qSlicerAbstractModuleRepresentation* qSlicerGltfSupportModule
::createWidgetRepresentation()
{
  return new qSlicerGltfSupportModuleWidget;
}

//-----------------------------------------------------------------------------
vtkMRMLAbstractLogic* qSlicerGltfSupportModule::createLogic()
{
  return vtkSlicerGltfSupportLogic::New();
}
