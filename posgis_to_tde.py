###
# @sarahbat
# Read data from Postgres and write to TDE
#
# Using Psychopg2 library - https://wiki.postgresql.org/wiki/Using_psycopg2_with_PostgreSQL#Perform_a_Select
#
###

import psycopg2
from tableausdk import *
from tableausdk.Extract import *

###
# Retrieve table from postgres and convert to TDE
###
def getTableFromPG(host, dbName, userName, pw, selectStatement):
    # Define our connection string
    conn_string = "host='" + host + \
                  "' dbname='" + dbName + \
                  "' user='" + userName + \
                  "' password='" + pw + "'"

    # print the connection string we will use to connect
    print("Connecting to database	->{0}").format(dbName)

    # get a connection, if a connect cannot be made an exception will be raised here
    conn = psycopg2.connect(conn_string)

    # conn.cursor will return a cursor object, you can use this cursor to perform queries
    cursor = conn.cursor()
    print("Connected!")

    # execute our Query
    cursor.execute(selectStatement)

    # retrieve the records from the database
    records = cursor.fetchall()

    print("There are {0} records and {1} columns in the table").format(len(records), len(records[0]))

    return records


###
# Convert table from postgres into a TDE
###
def writeTableToTDE(pgFields, pgData, extractLocation):
    print('writing table to ' + extractLocation)

    # 1. initialize a new extract
    ExtractAPI.initialize()

    # 2. Create a table definition
    new_extract = Extract(extractLocation)

    # 3. Add column definitions to the table definition
    table_definition = TableDefinition()
    for i in range(0, len(pgFields)):
        table_definition.addColumn(pgFields[i][0], pgFields[i][1])

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
    numberRecords = len(pgData)
    for i in range(0, numberRecords):
        # Note that this doesn't cover all possible TDE data types
        for j in range(0, len(pgFields)):
            if pgFields[j][1] == Type.INTEGER:
                new_row.setInteger(j, pgData[i][j])
            elif pgFields[j][1] == Type.UNICODE_STRING:
                new_row.setString(j, pgData[i][j])
            elif pgFields[j][1] == Type.SPATIAL:
                new_row.setSpatial(j, pgData[i][j])
            elif pgFields[j][i] == Type.BOOLEAN:
                new_row.setBoolean(j, pgData[i][j])
            elif pgFields[j][i] == Type.DOUBLE:
                new_row.setDouble(j, pgData[j][i])
        new_table.insert(new_row)  # Add the new row to the table

    # 7. Save the table and extract
    new_extract.close()

    # 8. Release the extract API
    ExtractAPI.cleanup()
    return



if __name__ == "__main__":
    selectStatement = "select gid, state, city, name, ST_AsText(geom) " \
                      "from zillowneighborhoods_seattle4326"

    table = getTableFromPG('localhost', 'redfin', 'postgres', 'postgres', selectStatement)

    outputTDE = "c:\\temp\\extract5.tde"

    tdeFields = [('gid', Type.INTEGER),
                    ('state', Type.UNICODE_STRING),
                    ('city', Type.UNICODE_STRING),
                    ('name', Type.UNICODE_STRING),
                    ('geometry', Type.SPATIAL)]

    writeTableToTDE(tdeFields, table, outputTDE)