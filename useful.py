import math

def prj_WMtoLL(x,y):
  # Check if coordinate out of range for Web Mercator
  # 20037508.3427892 is full extent of Web Mercator
  if (abs(x) > 20037508.3427892) or (abs(y) > 20037508.3427892):
    print("coordinates provided were out of range; maximum range for Web Mercator is +/-20037508.343")
    return

  semimajorAxis = 6378137.0  # WGS84 spheriod semimajor axis

  latitude = (1.5707963267948966 - (2.0 * math.atan(math.exp((-1.0 * y) / semimajorAxis)))) * (180 / math.pi)
  longitude = ((x / semimajorAxis) * 57.295779513082323) - \
              ((math.floor((((x / semimajorAxis) * 57.295779513082323) + 180.0) / 360.0)) * 360.0)

  return [longitude, latitude]

def prj_LLtoWM(lon, lat):
  return



###
# Write a TDE
# tdeFields = array of tuples [(fieldName, TDE type)]- e.g., :
#   [('gid', Type.INTEGER),
#     ('state', Type.UNICODE_STRING),
#     ('city', Type.UNICODE_STRING),
#     ('name', Type.UNICODE_STRING),
#     ('geometry', Type.SPATIAL)]
#
# tdeData = table of data
# extractLocation = path and name.tde
###
def writeTDE (tdeFields, tdeData, extractLocation):
  from tableausdk import *
  from tableausdk.Extract import *

  print("writing table to {0}").format(extractLocation)

  # 1. initialize a new extract
  ExtractAPI.initialize()

  # 2. Create a table definition
  new_extract = Extract(extractLocation)

  # 3. Add column definitions to the table definition
  table_definition = TableDefinition()
  for i in range(0, len(tdeFields)):
    table_definition.addColumn(tdeFields[i][0], tdeFields[i][1])

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
  numberRecords = len(tdeData)
  for i in range(0, numberRecords):
    # Note that this doesn't cover all possible TDE data types
    for j in range(0, len(tdeFields)):
      if tdeFields[j][1] == Type.INTEGER:
        new_row.setInteger(j, tdeData[i][j])
      elif tdeFields[j][1] == Type.UNICODE_STRING:
        new_row.setString(j, tdeData[i][j])
      elif tdeFields[j][1] == Type.SPATIAL:
        new_row.setSpatial(j, tdeData[i][j])
      elif tdeFields[j][i] == Type.BOOLEAN:
        new_row.setBoolean(j, tdeData[i][j])
      elif tdeFields[j][i] == Type.DOUBLE:
        new_row.setDouble(j, tdeData[j][i])
    new_table.insert(new_row)  # Add the new row to the table

  # 7. Save the table and extract
  new_extract.close()

  # 8. Release the extract API
  ExtractAPI.cleanup()
  return
