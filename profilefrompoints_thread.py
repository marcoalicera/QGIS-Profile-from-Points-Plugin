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

#import locale

from PyQt4.QtCore import *
from PyQt4.QtGui import *

from qgis.core import *

import profilefrompoints_utils as utils



import os


from pyspatialite import dbapi2 as db

class ProfilefromPointsThread(QThread):

    processFinished = pyqtSignal(list)
    processInterrupted = pyqtSignal()


    def __init__(self, point_layer,z_field,createLine,order_field,sort,line_layer,buff,selected_points,selected_line):
        QThread.__init__(self, QThread.currentThread())
        self.mutex = QMutex()
        self.stopMe = 0
        self.interrupted = False

        self.point_layer = point_layer
        self.z_field = z_field
        self.createLine = createLine
        self.order_field = order_field
        self.sort = sort
        self.line_layer = line_layer
        self.buff = buff
        self.selected_points = selected_points
        self.selected_line = selected_line

    def run(self):
        values = self.profileplotter()

        if not self.interrupted:
            self.processFinished.emit([values])
        else:
            self.processInterrupted.emit()

    def stop(self):
        self.mutex.lock()
        self.stopMe = 1
        self.mutex.unlock()

        QThread.wait(self)

    def profileplotter(self):
        
#output path for spaitialite database
        outpath= os.path.join( os.environ['HOME'],'Desktop' )
        layer = self.point_layer
        #get crs of point layer
        crs=int(layer.crs().authid().split(':')[1])
        
        #get name of layer
        point_layer_name=self.point_layer.name()
        
        tmp_point_layer_name='tmp_'+point_layer_name
        #database import options
        options = {}
        options['overwrite'] = True
        options['forceSinglePartGeometryType'] = True
        #create database w/ tmp_ prefix
        dbase=os.path.join(outpath,tmp_point_layer_name+'.sqlite')
        
        #setup connection
        conn = db.connect(dbase)
        # creating a Cursor
        cur = conn.cursor()
        # initializing Spatial MetaData
        # using v.2.4.0 this will automatically create
        # GEOMETRY_COLUMNS and SPATIAL_REF_SYS
        sql = 'SELECT InitSpatialMetadata()'
        cur.execute(sql)
        conn.commit()
        conn.close()
        #import profile line into spatialite database
        uri = QgsDataSourceURI()
        uri.setDatabase(dbase)
        uri.setDataSource('',point_layer_name,'GEOMETRY')
        ret, errMsg = QgsVectorLayerImport.importLayer(layer, uri.uri(), 'spatialite', layer.crs(), self.selected_points, False, options)
#        else:
#            #create database w/ tmp_ prefix
#              QgsVectorFileWriter.writeAsVectorFormat(layer, dbase, "utf-8", layer.crs(), "SQLite", self.selected_points, None ,["SPATIALITE=YES"])
        
        #setup connection
        conn = db.connect(dbase)
        cur = conn.cursor()
        
        if self.createLine:
            self.buff = 0
            #check if table exists
            sql = "SELECT tbl_name FROM sqlite_master WHERE tbl_name LIKE 'line_{}' ".format(point_layer_name)
            cur.execute(sql)
            if cur.fetchone:
                sql = "DROP TABLE IF EXISTS line_{}".format(point_layer_name)
                cur.execute(sql)
                sql = "SELECT DiscardGeometryColumn ('line_{}','GEOMETRY')".format(point_layer_name)
                cur.execute(sql)
                conn.commit()
            sql = "CREATE TABLE 'line_{}' AS SELECT 1 as OGC_FID, MakeLine(GEOMETRY) as GEOMETRY FROM (SELECT {}, {}, GEOMETRY FROM '{}' ORDER BY {} {}) mypoints".format(point_layer_name, self.order_field,self.z_field,point_layer_name,self.order_field,self.sort)
            print sql
            cur.execute(sql)
            conn.commit()
            
            sql = "SELECT RecoverGeometryColumn('line_{}','GEOMETRY',{},'LINESTRING','XY')".format(point_layer_name,crs)
            cur.execute(sql)
            conn.commit()
            
            line_layer_name = 'line_'+point_layer_name
    
        else:
            options = {}
            options['overwrite'] = True
            options['forceSinglePartGeometryType'] = True
            #import profile line into spatialite database
            layer = self.line_layer
            line_layer_name = layer.name()
            uri = QgsDataSourceURI()
            uri.setDatabase(dbase)
            uri.setDataSource('',line_layer_name,'GEOMETRY')
            ret, errMsg = QgsVectorLayerImport.importLayer(layer, uri.uri(), 'spatialite', layer.crs(), self.selected_line, False, options)
    
        # station points along line
        sql = "SELECT st_line_locate_point(myline.GEOMETRY,myselectedpoints.GEOMETRY)*st_length(myline.GEOMETRY) as station, {} as elevation FROM {} myline, (SELECT mypoints.* FROM {} mypoints, {} myline WHERE ST_Intersects(mypoints.geometry,ST_BUFFER(myline.geometry,{}))) myselectedpoints ORDER BY station".format(self.z_field,line_layer_name,point_layer_name,line_layer_name,self.buff)
        print sql
        cur.execute(sql)
    
        
        # get values
        station=[]
        elevation=[]    
        for i in cur:
            station.append(i[0])
            elevation.append(i[1])
        values = [station,elevation]

        #print values
        # create station elevation table
        #check if table exists
        sql = "SELECT tbl_name FROM sqlite_master WHERE tbl_name LIKE 'profile_{}' ".format(point_layer_name)
        cur.execute(sql)
        if cur.fetchone:
            sql = "DROP TABLE IF EXISTS profile_{}".format(point_layer_name)
            cur.execute(sql)
            sql = "SELECT DiscardGeometryColumn ('profile_{}','GEOMETRY')".format(point_layer_name)
            cur.execute(sql)
            conn.commit()
        
        sql = "CREATE TABLE profile_{} AS SELECT myselectedpoints.*,st_line_locate_point(myline.GEOMETRY,myselectedpoints.GEOMETRY)*st_length(myline.GEOMETRY) as station, {} as elevation FROM {} myline, (SELECT mypoints.* FROM {} mypoints, {} myline WHERE ST_Intersects(mypoints.geometry,ST_BUFFER(myline.geometry,{}))) myselectedpoints ORDER BY station".format(point_layer_name,self.z_field,line_layer_name,point_layer_name,line_layer_name,self.buff)
        print sql
        cur.execute(sql)
        conn.commit()
        
        
        sql = "SELECT RecoverGeometryColumn('{}','GEOMETRY',{},'POINT','XY')".format('profile_'+point_layer_name,crs)
        cur.execute(sql)
        conn.commit()
        

        conn.close()
    
        
        return values