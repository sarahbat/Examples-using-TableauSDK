###
# @sarahbat (Sarah Battersby - sbattersby@tableau.com)
#
# Read origin-destination lat/lon pairs from a CSV file & calculate great circle arcs
#
# Python = 2.7
###

from tableausdk import Type
from tableausdk.Extract import *
from geographiclib.geodesic import Geodesic
import csv


# Where the origin data comes from
csvLocation = 'data/flightsoftheworld.csv'

# Where the TDE will be written
extractLocation = 'all_flight_paths.tde'

# csv column number for origin/destination coordinates (start count at 0 for the first col in your csv)
ORIG_LAT = 1
ORIG_LON  = 2
DEST_LAT =  3
DEST_LON =  4
SEG_NAME = 5

#####################################################################
## Process the data and write the TDE
#####################################################################

# 1. initialize a new extract
ExtractAPI.initialize()

# 2. Create a table definition
new_extract = Extract(extractLocation)

# 3. Add column definitions to the table definition
table_definition = TableDefinition()
table_definition.addColumn('route', Type.UNICODE_STRING)  # column 0
table_definition.addColumn('geometry', Type.SPATIAL)
table_definition.addColumn('distance_km', Type.DOUBLE)

# 4. Initialize a new table in the extract
if (new_extract.hasTable('Extract') == False):
  new_table = new_extract.addTable('Extract', table_definition)
else:
  new_table = new_extract.openTable('Extract')

# 5. Create a new row
new_row = Row(table_definition)  # Pass the table definition to the constructor

# 6. walk through the origin/destination data from CSV, write each path to TDE
with open(csvLocation, 'rb') as csvfile:
  csvreader = csv.reader(csvfile, delimiter=',')

  next(csvreader) # skip header

  for row in csvreader:
    olat = float(row[ORIG_LAT])
    olon = float(row[ORIG_LON])
    dlat = float(row[DEST_LAT])
    dlon = float(row[DEST_LON])
    route = row[SEG_NAME]

    p = Geodesic.WGS84.Inverse(olat, olon, dlat, dlon)
    l = Geodesic.WGS84.Line(p['lat1'], p['lon1'], p['azi1'])
    if (p['s12'] >= 1000000):
      num = int(p['s12'] / 100000)
    else:
      num = 10
    output = ''
    linestring = 'LINESTRING('
    for i in range(num + 1):
      b = l.Position(i * p['s12'] / num, Geodesic.STANDARD | Geodesic.LONG_UNROLL)
      output += repr(b['lon2']) + ',' + repr(b['lat2']) + ', '
      linestring += str(b['lon2']) + ' ' + str(b['lat2']) + ', '
    # remove the ',' after the last coordinate and close the WKT string with a ')'
    linestring = linestring[:-2] + ')'

    new_row.setString(0, route)
    new_row.setSpatial(1, linestring)
    new_row.setDouble(2, p['s12']/1000) # meters to KM
    new_table.insert(new_row)

# 7. Save the table and extract
new_extract.close()

# 8. Release the extract API
ExtractAPI.cleanup()

print 'Finished!  Enjoy your TDE'
