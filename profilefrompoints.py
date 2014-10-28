# -*- coding: utf-8 -*-
"""
/***************************************************************************
 ProfilefromPoints
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
# Import the PyQt and QGIS libraries
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from qgis.core import *
from qgis.gui import *
# Initialize Qt resources from file resources.py
import resources_rc
# Import the code for the dialog
#from profilefrompointsdialog import ProfilefromPointsDialog
import profilefrompointsdialog
import profilefrompoints_utils as utils
import os.path


class ProfilefromPoints:

    def __init__(self, iface):
        # Save reference to the QGIS interface
        self.iface = iface
        # initialize plugin directory
        self.plugin_dir = os.path.dirname(__file__)
        # initialize locale
        locale = QSettings().value("locale/userLocale")[0:2]
        localePath = os.path.join(self.plugin_dir, 'i18n', 'profilefrompoints_{}.qm'.format(locale))

        if os.path.exists(localePath):
            self.translator = QTranslator()
            self.translator.load(localePath)

            if qVersion() > '4.3.3':
                QCoreApplication.installTranslator(self.translator)

        # Create the dialog (after translation) and keep reference
        #self.dlg = ProfilefromPointsDialog()

    def initGui(self):
        # Create action that will start plugin configuration
        self.action = QAction(
            QIcon(":/plugins/profilefrompoints/icon.png"),
            u"Profile from points", self.iface.mainWindow())
        # connect the action to the run method
        self.action.triggered.connect(self.run)

        # Add toolbar button and menu item
        self.iface.addToolBarIcon(self.action)
        self.iface.addPluginToMenu(u"&Profile from Points", self.action)

    def unload(self):
        # Remove the plugin menu item and icon
        self.iface.removePluginMenu(u"&Profile from Points", self.action)
        self.iface.removeToolBarIcon(self.action)

    # run method that performs all the real work
    def run(self):
        layersCount = len(utils.getPointLayerNames())
        if layersCount == 0:
            self.iface.messageBar().pushMessage(QCoreApplication.translate("ProfilefromPoints", "Project doesn't have any vector point layers"))
            return
#        self.dlg = profilefrompointsdialog.ProfilefromPointsDialog(self.iface)

        d = profilefrompointsdialog.ProfilefromPointsDialog(self.iface)
        d.show()
        d.exec_()




#        # Run the dialog event loop
#        result = self.dlg.exec_()
#        # See if OK was pressed
#        if result == 1:
#            # do something useful (delete the line containing pass and
#            # substitute with your code)
#            pass
#        self.dlg.uPointLayer.clear()
