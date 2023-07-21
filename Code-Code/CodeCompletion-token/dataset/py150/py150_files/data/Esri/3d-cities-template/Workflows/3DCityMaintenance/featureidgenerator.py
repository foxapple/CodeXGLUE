# ------------------------------------------------------------------------------
# 3D City Information Model Python Toolbox/FeatureIdGenerator
# 1.2.0_2013-06-14
#
#
# Author: Thorsten Reitz, ESRI R&D Lab Zurich
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
# ------------------------------------------------------------------------------

import arcpy

class FeatureIdGenerator(object):
    def __init__(self):
        self.label = "3DCIM Feature ID Generator"
        self.description = "This tool adds Feature ID fields and values to any " +\
                            "Feature Classes in an input workspace (File GDB), which are used as persistent " +\
                            "identifiers for referencing of 3DCIM features."
        self.canRunInBackground = False

    def getParameterInfo(self):
        # Define parameter definitions

        # Input Geodatabase parameter
        in_gdb = arcpy.Parameter(
            displayName="Input Workspace",
            name="in_gdb",
            datatype="Workspace",
            parameterType="Required",
            direction="Input")


        # Generation Method Field parameter
        generation_field = arcpy.Parameter(
            displayName="3DCIM Schema Version",
            name="schema_version",
            datatype="String",
            parameterType="Required",
            direction="Input")

        # Set a value list for the Generation method
        generation_field.filter.type = "ValueList"
        generation_field.filter.list = ["1.3", "1.4", "1.5"]
        generation_field.value = "1.5"

        # Interval Size Field parameter
        hi_batchsize_field = arcpy.Parameter(
            displayName="Interval size",
            name="hi_batchsize",
            datatype="Long",
            parameterType="Required",
            direction="Input")

        hi_batchsize_field.value = 20000

        # Derived Output Features parameter
        out_gdb = arcpy.Parameter(
            displayName="Output Workspace",
            name="out_gdb",
            datatype="Workspace",
            parameterType="Derived",
            direction="Output")

        out_gdb.parameterDependencies = [in_gdb.name]

        parameters = [in_gdb, generation_field, hi_batchsize_field, out_gdb]

        return parameters

    def isLicensed(self):
        """Set whether tool is licensed to execute."""
        return True

    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""
        return

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter.  This method is called after internal validation."""
        return

    def execute(self, parameters, messages):
        """The source code of the tool."""

        arcpy.env.workspace = parameters[0].value
        schema_version = parameters[1].value

        # Number of low IDs per hi ID
        # Higher batch sizes mean less updating of the table, lower batch sizes more
        # efficient ID usage especially when multiple processes access the table.
        hi_batchsize = parameters[2].value

        # Name of the table used to maintain hi/lo counter status per feature class. Value depends on schema version.
        generate_ID_table_name = "GenerateID"
        seqnameField = "name"
        seqcounterField = "hi"
        seqintervalField = "low"
        if schema_version == "1.4" or schema_version == "1.5":
            generate_ID_table_name = "GenerateId"
            seqnameField = "SEQNAME"
            seqcounterField = "SEQCOUNTER"
            seqintervalField = "SEQINTERV"

        # check whether sequences table has already been created and create if not.
        new_table = None
        counter_tbl_list = arcpy.ListTables(generate_ID_table_name)
        if not counter_tbl_list:
            arcpy.AddMessage("Creating new " + generate_ID_table_name +" table.")
            new_table = True
            generate_ID_table = arcpy.CreateTable_management(arcpy.env.workspace, generate_ID_table_name)
            if schema_version == "1.3":
                arcpy.AddField_management(generate_ID_table, seqnameField, "TEXT", None, None, 50, "Feature Class Name", "NON_NULLABLE", "REQUIRED")
                arcpy.AddField_management(generate_ID_table, seqcounterField, "LONG", None, None, None, "Hi counter", "NON_NULLABLE", "REQUIRED")
                arcpy.AddField_management(generate_ID_table, seqintervalField, "LONG", None, None, None, "Low counter", "NON_NULLABLE", "REQUIRED")
            if schema_version == "1.4" or schema_version == "1.5": # identical schema to attribute assistant
                arcpy.AddField_management(generate_ID_table, seqnameField, "TEXT", None, None, 50, "Sequence Name", "NON_NULLABLE", "NON_REQUIRED")
                arcpy.AddField_management(generate_ID_table, seqcounterField, "LONG", None, None, None, "Sequence Counter", "NON_NULLABLE", "NON_REQUIRED")
                arcpy.AddField_management(generate_ID_table, seqintervalField, "SHORT", None, None, None, "Interval Value", "NULLABLE", "NON_REQUIRED")
                arcpy.AddField_management(generate_ID_table, "COMMENTS", "TEXT", None, None, 255, "Comments", "NULLABLE", "NON_REQUIRED")
        else:
            new_table = False
            generate_ID_table = counter_tbl_list[0]

        # go through feature classes to create FIDs where needed.
        fc_list = arcpy.ListFeatureClasses()
        for fc in fc_list:
            arcpy.AddMessage("Processing " + fc)
            counter = 0 # counter in this session, range is always 0 ... [interval - 1]
            baseCount = 0 # value
            interval = hi_batchsize # batchsize/interval size

            # if we only created the GenerateID table, we know we have to insert the counter.
            if new_table:
                insert_new_counter_cursor = arcpy.da.InsertCursor(generate_ID_table_name, [seqnameField, seqcounterField, seqintervalField])
                insert_new_counter_cursor.insertRow((fc, 0, hi_batchsize))
                del insert_new_counter_cursor

            # check if a counter of fc_name exists and retrieve value
            counterParams = None
            escaped_name = arcpy.AddFieldDelimiters(generate_ID_table_name, seqnameField)
            where_clause = escaped_name + " = " + "'" + fc + "'"
            with arcpy.da.SearchCursor(generate_ID_table_name, [seqnameField, seqcounterField, seqintervalField], where_clause) as rows:
                for counterRow in rows:
                    counterParams = counterRow
                    break

            if counterParams != None:
                baseCount = counterParams[1]
                interval = counterParams[2]
            else:
                # create that counter
                insert_new_counter_cursor = arcpy.da.InsertCursor(generate_ID_table_name, [seqnameField, seqcounterField, seqintervalField])
                insert_new_counter_cursor.insertRow((fc, 0, hi_batchsize))
                del insert_new_counter_cursor

            with arcpy.da.SearchCursor(generate_ID_table_name, [seqnameField, seqcounterField, seqintervalField]) as rows:
                for row in rows:
                    if row[0] == fc:
                        baseCount = row[1]
                        interval = row[2]
                        break

            # increment counter to indicate that it is in active usage
            self.incrementCounter(generate_ID_table_name, seqnameField, seqcounterField, fc, baseCount + interval)

            # check if feature class already has a FID, add it if not.
            fid_name = fc + "FID"
            fields_list = arcpy.ListFields(fc, fid_name)
            if not fields_list:
                arcpy.AddField_management(fc, fid_name, "TEXT", None, None, 50, "Feature ID", None, None)

            # modify FID of object if required
            with arcpy.da.UpdateCursor(fc, [fid_name]) as rows:
                for row in rows:
                    if row[0] == None:
                        if counter >= interval:
                            # get new baseCount from GenerateId
                            arcpy.AddMessage("Interval exhausted, getting next Interval.")
                            with arcpy.da.SearchCursor(generate_ID_table_name, [seqcounterField], where_clause) as rows:
                                for counterRow in rows:
                                    baseCount = counterRow[0]
                                    break

                            # Reset local counter
                            counter = 0
                        row[0] = fc + "/" + str(baseCount + counter)
                        counter += 1
                        rows.updateRow(row)

            # write back the new counter value to the GenerateID table.
            with arcpy.da.UpdateCursor(generate_ID_table_name, [seqnameField, seqcounterField]) as rows:
                for newRow in rows:
                    if newRow[0] == fc:
                        newRow[1] = baseCount + counter
                        rows.updateRow(newRow)
                        break

        arcpy.AddMessage("Completed adding of Feature IDs.")
        return

    def incrementCounter(self, generate_ID_table_name, seqnameField, seqcounterField, fcName, newCount):
        # update counter in GenerateId table
        with arcpy.da.UpdateCursor(generate_ID_table_name, [seqnameField, seqcounterField]) as rows:
            for row in rows:
                if row[0] == fcName:
                    row[1] = newCount
                    rows.updateRow(row)
                    break