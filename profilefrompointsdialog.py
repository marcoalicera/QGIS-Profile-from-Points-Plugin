# -*- coding: utf-8 -*-
"""
/***************************************************************************
 ProfilefromPointsDialog
                                 A QGIS plugin
 Plots a profile from point survey data using a temporary spatialite database
                             -------------------
        begin                : 2014-10-15
        copyright            : (C) 2014 by Mitchell Weier - North Dakota State Water Commission
        email                : mweier@nd.gov
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from qgis.core import *
#from qgis.gui import *
from ui_profilefrompoints import Ui_ProfilefromPoints

#import qgis.utils

import os 

from ui_profilefrompoints import Ui_ProfilefromPoints
 
import profilefrompoints_thread
import profilefrompoints_utils as utils

import numpy as np
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt4agg import NavigationToolbar2QTAgg as NavigationToolbar
from matplotlib.figure import Figure
from matplotlib import rcParams
from matplotlib.ticker import ScalarFormatter

import processing

# create the dialog


class ProfilefromPointsDialog(QDialog, Ui_ProfilefromPoints):
    def __init__(self,iface):
        QDialog.__init__(self)
        # Set up the user interface from Designer.
        # After setupUI you can access any designer object by doing
        # self.<objectname>, and you can use autoconnect slots - see
        # http://qt-project.org/doc/qt-4.8/designer-using-a-ui-file.html
        # #widgets-and-dialogs-with-auto-connect
        self.iface = iface
        
        self.setupUi(self)
        
        # add matplotlib figure to dialog
        self.figure = Figure()
        self.axes = self.figure.add_subplot(111)
        self.canvas = FigureCanvas(self.figure)
        
        self.mpltoolbar = NavigationToolbar(self.canvas, self.widgetPlot)
        lstActions = self.mpltoolbar.actions()
        self.mpltoolbar.removeAction(lstActions[7])
        self.layoutPlot.addWidget(self.canvas)
        self.layoutPlot.addWidget(self.mpltoolbar)
        self.figure.patch.set_visible(False)
        
        # and configure matplotlib params
        rcParams["font.serif"] = "Verdana, Arial, Liberation Serif"
        rcParams["font.sans-serif"] = "Tahoma, Arial, Liberation Sans"
        rcParams["font.cursive"] = "Courier New, Arial, Liberation Sans"
        rcParams["font.fantasy"] = "Comic Sans MS, Arial, Liberation Sans"
        rcParams["font.monospace"] = "Courier New, Liberation Mono"

        self.values = None

        self.btnOk = self.buttonBox.button(QDialogButtonBox.Ok)
        self.btnClose = self.buttonBox.button(QDialogButtonBox.Close)

        self.uPointLayer.currentIndexChanged.connect(self.reloadFields)
        self.uLineLayer.currentIndexChanged.connect(self.checkSelectedLine)
        self.uCopytoClip.clicked.connect(self.copyClipboard)


        self.manageGui()

        
        
    def manageGui(self):
        print 'manageGui'
        self.uPointLayer.clear()
        self.uPointLayer.addItems(utils.getPointLayerNames())
        self.uLineLayer.clear()
        self.uLineLayer.addItems(utils.getLineLayerNames())

    
    def reloadFields(self):
        print 'reload fields'
        self.uZfield.clear()
        self.uOrderField.clear()

        self.axes.clear()

        point_layer = processing.getObject(str(self.uPointLayer.currentText()))
        if point_layer.selectedFeatureCount() != 0:
            self.uSelectedPoints.setCheckState(Qt.Checked)
        else:
            self.uSelectedPoints.setCheckState(Qt.Unchecked)
        
        self.uZfield.addItems(utils.getFieldNames(point_layer, [QVariant.Int, QVariant.Double]))
        self.uOrderField.addItems(utils.getFieldNames(point_layer, [QVariant.Int, QVariant.Double]))

    def checkSelectedLine(self):
        print 'check if line layer selected'
        line_layer = processing.getObject(str(self.uLineLayer.currentText()))
        if line_layer:
            if line_layer.selectedFeatureCount() != 0:
                self.uSelectedLine.setCheckState(Qt.Checked)
            else:
                self.uSelectedLine.setCheckState(Qt.Unchecked)

             
    def accept(self):
        print 'accepted'
        
        self.axes.clear()

        point_layer = processing.getObject(self.uPointLayer.currentText())
        line_layer = processing.getObject(self.uLineLayer.currentText())
        z_field=(self.uZfield.currentText())
        order_field=str(self.uOrderField.currentText())
        if str(self.uOrder.currentText())=='Ascending':
            sort = 'ASC'
        else:
            sort = 'DESC'
        buff=float(self.uBuffer.displayText())
        
        if self.utabWidget.currentIndex()==0:
            createLine=True        
        else:
            createLine=False
        



        if self.uSelectedPoints.isChecked() and \
                point_layer.selectedFeatureCount() == 0 or self.uSelectedLine.isChecked() and \
                line_layer.selectedFeatureCount() == 0:
            QMessageBox.warning(self,
                                self.tr('No selection'),
                                self.tr('There is no selection in input '
                                        'layer. Uncheck corresponding option '
                                        'or select some features before '
                                        'running analysis'))
            return
        
        if not createLine and not self.uSelectedLine.isChecked() and \
                line_layer.featureCount() != 1:
            QMessageBox.warning(self,
                                self.tr('Line Layer Error'),
                                self.tr('There are multiple line features within the line layer.\n Please select one.'))
            return
        
        if utils.checkMultipart(point_layer):
            QMessageBox.warning(self,
                                self.tr('Point Layer Error'),
                                self.tr('Point layer has multi-part geometery.\n Please convert to single part geometery.'))
            return
            
        if not createLine and utils.checkMultipart(line_layer):
            QMessageBox.warning(self,
                                self.tr('Line Layer Error'),
                                self.tr('Line layer has multi-part geometery.\n Please convert to single part geometery.'))
            return
        
        selected_points = self.uSelectedPoints.checkState()
        selected_line = self.uSelectedLine.checkState()

        self.workThread = profilefrompoints_thread.ProfilefromPointsThread(point_layer,z_field,createLine,order_field,sort,line_layer,buff,selected_points,selected_line)
        

        self.workThread.processFinished.connect(self.processFinished)
        self.workThread.processInterrupted.connect(self.processInterrupted)

        self.btnOk.setEnabled(False)
        self.btnClose.setText(self.tr("Cancel"))
        self.buttonBox.rejected.disconnect(self.reject)
        self.btnClose.clicked.connect(self.stopProcessing)
        
        self.uprogressBar.setMaximum(0)
        self.workThread.start()
        
        self.dbase=os.path.join( os.environ['HOME'],'Desktop','tmp_'+point_layer.name()+'.sqlite')

        
    def reject(self):
        print 'rejected'
        QDialog.reject(self)



    def processFinished(self, values):
        self.stopProcessing()
        self.values = values[0]
        self.uCopytoClip.setEnabled(True)
        self.iface.messageBar().pushMessage(QCoreApplication.translate("ProfilefromPoints", 'Profile from Points  - A temporary spatialite database was created at {}.  Please delete when finished'.format(self.dbase)))
      

        # create plot
        self.refreshPlot()

        self.restoreGui()

    def processInterrupted(self):
        self.restoreGui()

    def stopProcessing(self):
        if self.workThread is not None:
            self.workThread.stop()
            self.workThread = None

    def restoreGui(self):
        self.buttonBox.rejected.connect(self.reject)
        self.btnClose.clicked.disconnect(self.stopProcessing)
        self.btnClose.setText(self.tr("Close"))
        self.btnOk.setEnabled(True)
        self.uprogressBar.setMaximum(100)

    def refreshPlot(self):
        self.axes.clear()

        if self.values is None:
            return

        self.axes.plot(np.array(self.values[0]),np.array(self.values[1]))
        self.axes.grid()
        formatter = ScalarFormatter(useOffset=False)
        self.axes.yaxis.set_major_formatter(formatter)

        self.axes.set_ylabel(unicode(self.tr("Elevation, z field units")))
        self.axes.set_xlabel(unicode(self.tr('Station, layer units')))

        self.canvas.draw()    
            
    def copyClipboard (self):
        if self.values is None:
            return
        else:
            clipboard = QApplication.clipboard()
            clipboard.setText('\n'.join('%s\t%s' % x for x in zip(self.values[0],self.values[1])))
