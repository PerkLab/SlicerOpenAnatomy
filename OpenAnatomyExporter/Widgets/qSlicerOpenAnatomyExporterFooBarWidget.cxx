/*==============================================================================

  Program: 3D Slicer

  Copyright (c) Kitware Inc.

  See COPYRIGHT.txt
  or http://www.slicer.org/copyright/copyright.txt for details.

  Unless required by applicable law or agreed to in writing, software
  distributed under the License is distributed on an "AS IS" BASIS,
  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
  See the License for the specific language governing permissions and
  limitations under the License.

  This file was originally developed by Jean-Christophe Fillion-Robin, Kitware Inc.
  and was partially funded by NIH grant 3P41RR013218-12S1

==============================================================================*/

// FooBar Widgets includes
#include "qSlicerOpenAnatomyExporterFooBarWidget.h"
#include "ui_qSlicerOpenAnatomyExporterFooBarWidget.h"

//-----------------------------------------------------------------------------
/// \ingroup Slicer_QtModules_OpenAnatomyExporter
class qSlicerOpenAnatomyExporterFooBarWidgetPrivate
  : public Ui_qSlicerOpenAnatomyExporterFooBarWidget
{
  Q_DECLARE_PUBLIC(qSlicerOpenAnatomyExporterFooBarWidget);
protected:
  qSlicerOpenAnatomyExporterFooBarWidget* const q_ptr;

public:
  qSlicerOpenAnatomyExporterFooBarWidgetPrivate(
    qSlicerOpenAnatomyExporterFooBarWidget& object);
  virtual void setupUi(qSlicerOpenAnatomyExporterFooBarWidget*);
};

// --------------------------------------------------------------------------
qSlicerOpenAnatomyExporterFooBarWidgetPrivate
::qSlicerOpenAnatomyExporterFooBarWidgetPrivate(
  qSlicerOpenAnatomyExporterFooBarWidget& object)
  : q_ptr(&object)
{
}

// --------------------------------------------------------------------------
void qSlicerOpenAnatomyExporterFooBarWidgetPrivate
::setupUi(qSlicerOpenAnatomyExporterFooBarWidget* widget)
{
  this->Ui_qSlicerOpenAnatomyExporterFooBarWidget::setupUi(widget);
}

//-----------------------------------------------------------------------------
// qSlicerOpenAnatomyExporterFooBarWidget methods

//-----------------------------------------------------------------------------
qSlicerOpenAnatomyExporterFooBarWidget
::qSlicerOpenAnatomyExporterFooBarWidget(QWidget* parentWidget)
  : Superclass( parentWidget )
  , d_ptr( new qSlicerOpenAnatomyExporterFooBarWidgetPrivate(*this) )
{
  Q_D(qSlicerOpenAnatomyExporterFooBarWidget);
  d->setupUi(this);
}

//-----------------------------------------------------------------------------
qSlicerOpenAnatomyExporterFooBarWidget
::~qSlicerOpenAnatomyExporterFooBarWidget()
{
}
