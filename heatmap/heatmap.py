###
# @sarahbat
#
# Heatmap to TDE demo
# Calculates heat map, returns rectangular polygon for each 'cell' and writes as WKT to TDE
#
# Data input is a shapefile, but could easily be modified to read in csv or other format
# with lat/lon values
#
# Python = 2.7
###

import geopandas as gpd
import numpy as np
from scipy import ndimage
from tableausdk import *
from tableausdk.Extract import *
import math


def main():

  pointDataLocation = 'data\\building_permits.shp'
  print('reading point data...')
  pointGdf = gpd.GeoDataFrame.from_file(pointDataLocation)

  # heatmap for events (based on kernel density estimation)
  print('setting up heatmap...')
  # get bbox for point input to make sure that the number of bins is correct both x and y
  pointBounds = pointGdf.to_crs({'init': 'epsg:3857'}).total_bounds # set coordinate reference system
  binSize = 250  # in WM meters
  xBinCount = int(math.ceil((math.fabs(pointBounds[0] - pointBounds[2]) / binSize)))
  yBinCount = int(math.ceil((math.fabs(pointBounds[1] - pointBounds[3]) / binSize)))

  smooth = [1.5, 3, 5]
  for smoothIdx in range(0, len(smooth)):
    print('creating heatmap with smoothing of ' + str(smooth[smoothIdx]))
    hm, extent = heatmap(pointGdf.to_crs({'init': 'epsg:3857'}), bins=[yBinCount, xBinCount],
                         smoothing=smooth[smoothIdx])

    extract_location = 'C:\\Users\\sbattersby\\PycharmProjects\\TableauSDK\\heatmap\\output\\'
    extract_name = 'heatMapExtract_vegas' + str(binSize) + 'm2.tde'
    heatmapToTDE(hm, extent, smooth[smoothIdx], extract_location + extract_name)

  print('Enjoy your heatmap!')

########################
# shapely point to WM
def wmToLL(x,y):
  # Check if coordinate out of range for Web Mercator
  # 20037508.3427892 is full extent of Web Mercator
  if (abs(x) > 20037508.3427892) or (abs(y) > 20037508.3427892):
    return

  semimajorAxis = 6378137.0  # WGS84 spheriod semimajor axis

  latitude = (1.5707963267948966 - (2.0 * math.atan(math.exp((-1.0 * y) / semimajorAxis)))) * (180 / math.pi)
  longitude = ((x / semimajorAxis) * 57.295779513082323) - (
  (math.floor((((x / semimajorAxis) * 57.295779513082323) + 180.0) / 360.0)) * 360.0)

  return [longitude, latitude]


def getFourCorners(centerPt, xSide, ySide):
  cx = centerPt[0]
  cy = centerPt[1]
  halfSideX = 0.5 * xSide
  halfSideY = 0.5 * ySide

  ul = wmToLL(cx - halfSideX, cy + halfSideY)
  ur = wmToLL(cx + halfSideX, cy + halfSideY)
  lr = wmToLL(cx + halfSideX, cy - halfSideY)
  ll = wmToLL(cx - halfSideX, cy - halfSideY)


  wkt = 'POLYGON((' + str(ul[0]) + ' ' + str(ul[1])+ ', ' + \
                      str(ur[0]) + ' ' + str(ur[1])+ ', ' + \
                      str(lr[0]) + ' ' + str(lr[1]) + ', ' + \
                      str(ll[0]) + ' ' + str(ll[1]) +  ', ' + \
                      str(ul[0]) + ' ' + str(ul[1])+ '))'

  return wkt


# heatmap function which takes a GeoDataFrame with point geometries and shows a matplotlib plot of heatmap density.
# http://nbviewer.jupyter.org/gist/perrygeo/c426355e40037c452434
# doing slighly bad things with the data here because of Web Mercator
# - switch to WM then back to WGS so the 'squares' line up
def heatmap (d, bins=(100, 100), smoothing=1.3, cmap='jet'):
  def getx (pt):
    return pt.coords[0][0]

  def gety (pt):
    return pt.coords[0][1]

  x = list(d.geometry.apply(getx))
  y = list(d.geometry.apply(gety))
  heatmap, xedges, yedges = np.histogram2d(y, x, bins=bins)
  extent = [yedges[0], yedges[-1], xedges[-1], xedges[0]]  # bin edges along the x and y dimensions, ordered

  # why are we taking log?
  logheatmap = np.log(heatmap)
  logheatmap[np.isneginf(logheatmap)] = 0
  logheatmap = ndimage.filters.gaussian_filter(logheatmap, smoothing, mode='nearest')


  return (logheatmap, extent)

def heatmapToTDE(heatmap, extent, smoothing, extractLocation):


  xLen = len(heatmap)
  yLen = len(heatmap[0])
  xRange = abs(extent[0] - extent[1])
  yRange = abs(extent[2] - extent[3])
  xMin = min(extent[0], extent[1])
  yMin = min(extent[2], extent[3])
  xIncrement = xRange / yLen
  yIncrement = yRange / xLen

  # 1. initialize a new extract
  ExtractAPI.initialize()

  # 2. Create a table definition
  new_extract = Extract(extractLocation)

  # 3. Add column definitions to the table definition
  table_definition = TableDefinition()
  table_definition.addColumn('ROW', Type.UNICODE_STRING)  # column 0
  table_definition.addColumn('COL', Type.UNICODE_STRING)  # column 1
  table_definition.addColumn('VALUE', Type.DOUBLE)  # column 2
  table_definition.addColumn('ID', Type.UNICODE_STRING)
  table_definition.addColumn('CellCount', Type.INTEGER)
  table_definition.addColumn('Smoothing', Type.DOUBLE)
  table_definition.addColumn('GEOM', Type.SPATIAL)

  # 4. Initialize a new table in the extract
  # a. check if the table already exists
  # Only add table if it doesn't already exist
  if (new_extract.hasTable('Extract') == False):
    new_table = new_extract.addTable('Extract', table_definition)
  else:
    new_table = new_extract.openTable('Extract')

  # 5. Create a new row
  new_row = Row(table_definition)  # Pass the table definition to the constructor

  # 6. Populate each new row
  yCoord = yMin
  for i in range(0, xLen):
    yCoord += yIncrement
    xCoord = xMin
    for j in range(0, yLen):
      xCoord += xIncrement

      cellWkt = getFourCorners([xCoord, yCoord], xIncrement, yIncrement)

      new_row.setString(0, str(i)) # ROW
      new_row.setString(1, str(j)) # COL
      new_row.setDouble(2, heatmap[i][j]) # VAL
      new_row.setString(3, str(i) + '-' + str(j)) # id
      new_row.setInteger(4, len(heatmap[0])) # cell count
      new_row.setDouble(5, smoothing) # smoothing
      new_row.setSpatial(6, cellWkt) # WKT spatial
      new_table.insert(new_row) # Add the new row to the table

  # 7. Save the table and extract
  new_extract.close()

  # 8. Release the extract API
  ExtractAPI.cleanup()
  return



if __name__ == "__main__":
  main()
