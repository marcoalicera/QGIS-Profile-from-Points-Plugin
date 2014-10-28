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
 This script initializes the plugin, making it known to QGIS.
"""

def classFactory(iface):
    # load ProfilefromPoints class from file ProfilefromPoints
    from profilefrompoints import ProfilefromPoints
    return ProfilefromPoints(iface)
