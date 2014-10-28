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

import locale

from PyQt4.QtCore import *
from PyQt4.QtGui import *

from qgis.core import *
from qgis.gui import *


def getPointLayerNames():
    layerMap = QgsMapLayerRegistry.instance().mapLayers()
    layerNames = []
    for name, layer in layerMap.iteritems():
        if layer.type() == QgsMapLayer.VectorLayer and layer.wkbType()==QGis.WKBPoint:
            layerNames.append(unicode(layer.name()))
    return sorted(layerNames, cmp=locale.strcoll)
    
def getLineLayerNames():
    layerMap = QgsMapLayerRegistry.instance().mapLayers()
    layerNames = []
    for name, layer in layerMap.iteritems():
        if layer.type() == QgsMapLayer.VectorLayer and layer.wkbType()==QGis.WKBLineString:
            layerNames.append(unicode(layer.name()))
    return sorted(layerNames, cmp=locale.strcoll)


def getVectorLayerByName(layerName):
    layerMap = QgsMapLayerRegistry.instance().mapLayers()
    for name, layer in layerMap.iteritems():
        if layer.type() == QgsMapLayer.VectorLayer and layer.name() == layerName:
            if layer.isValid():
                return layer
            else:
                return None


def getFieldNames(layer, fieldTypes):
    fields = layer.pendingFields()
    fieldNames = []
    for field in fields:
        if field.type() in fieldTypes and not field.name() in fieldNames:
            fieldNames.append(unicode(field.name()))
    return sorted(fieldNames, cmp=locale.strcoll)


def getFieldType(layer, fieldName):
    fields = layer.pendingFields()
    for field in fields:
        if field.name() == fieldName:
            return field.typeName()


def getUniqueValuesCount(layer, fieldIndex, useSelection):
    count = 0
    values = []
    if useSelection:
        for f in layer.selectedFeatures():
            if f[fieldIndex] not in values:
                values.append(f[fieldIndex])
                count += 1
    else:
        request = QgsFeatureRequest().setFlags(QgsFeatureRequest.NoGeometry)
        for f in layer.getFeatures(request):
            if f[fieldIndex] not in values:
                values.append(f[fieldIndex])
                count += 1
    return count

def checkMultipart(layer):
    for f in layer.getFeatures():
        if f.geometry().isMultipart():
            return True
    return False
    

#def is_number(s):
#    try:
#        float(s)
#        return True
#    except ValueError:
#        return False
        