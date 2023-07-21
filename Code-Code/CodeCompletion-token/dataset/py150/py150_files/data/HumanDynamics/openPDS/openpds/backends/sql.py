import ast
import sqlite3
import os
import stat
import threading
from openpds.core.models import Profile
from openpds.backends.base import InternalDataStore
from openpds import settings

INTERNAL_DATA_STORE_INSTANCES = {}

def dict_factory(cursor, row):
    dataRow = False
    d = {}
    v = {}
    for idx, col in enumerate(cursor.description):
        if col[0] == "time":
            dataRow = True
            d["time"] = row[idx]
        elif col[0] == "key": 
            d["key"] = row[idx]
        else:
            v[col[0]] = row[idx]
    if dataRow:
        d["value"] = v
    else:
        d = v
    return d

def getColumnDefForTable(table):
    return  ", ".join([ name + " " + dataType for (name, dataType) in table["columns"]])

def getCreateStatementForTable(table):
    columnDef = getColumnDefForTable(table)
    statement = "create table if not exists %s (%s)" % (table["name"], columnDef)
    return statement

class ListWithCount(list):
    def count(self):
        return len(self)

def getColumnValueFromRawData(rawData, columnName, tableDef, source="funf"):    
    return tableDef["mapping"][source][columnName](rawData) if "mapping" in tableDef and source in tableDef["mapping"] and columnName in tableDef["mapping"][source] else rawData[columnName] if columnName in rawData else None

class SQLInternalDataStore(InternalDataStore):
    LOCATION_TABLE = {
        "name": "LocationProbe",
        "columns": [
            ("mlatitude", "REAL"),
            ("mlongitude", "REAL"),
            ("maltitude", "REAL"), 
            ("maccuracy", "REAL"),
            ("mprovider", "TEXT")
        ]
    }

    ACTIVITY_TABLE = {
        "name": "ActivityProbe",
        "columns": [ 
            ("low_activity_intervals", "INTEGER"),
            ("high_activity_intervals", "INTEGER"),
            ("total_intervals", "INTEGER")
        ]
    }

    SCREEN_TABLE = {
        "name": "ScreenProbe",
        "columns": [
            ("screen_on", "INTEGER")
        ]
    }
   
    SMS_TABLE = {
        "name": "SmsProbe",
        "columns": [
            ("address", "TEXT"),
            ("person", "TEXT"),
            ("subject", "TEXT"),
            ("thread_id", "INTEGER"),
            ("body", "TEXT"),
            ("date", "BIGINT"),
            ("type", "INTEGER"),
            ("message_read", "INTEGER"),
            ("protocol", "INTEGER"),
            ("status", "INTEGER")
        ],
        "mapping": {
            "funf": {
                "message_read": lambda d: d["read"]
            }
        }
    }

    CALL_LOG_TABLE = {
        "name": "CallLogProbe",
        "columns": [
            ("_id", "INTEGER"),
            ("name", "TEXT"),
            ("number", "TEXT"),
            ("number_type", "TEXT"),
            ("date", "BIGINT"),
            ("type", "INTEGER"),
            ("duration", "INTEGER")
        ],
        "mapping": {
            "funf": {
                "number_type": lambda d: d["numbertype"]
            }
        }
    }

    BLUETOOTH_TABLE = {
        "name": "BluetoothProbe",
        "columns": [
            ("class", "INTEGER"),
            ("bt_mac", "TEXT"),
            ("name", "TEXT"),
            ("rssi", "INTEGER")
        ],
        "mapping": {
            "funf": {
                "bt_mac": lambda d: d["android-bluetooth-device-extra-device"]["maddress"],
                "class": lambda d: d["android-bluetooth-device-extra-class"]["mclass"],
                "name": lambda d: d.get("android-bluetooth-device-extra-name", None),
                "rssi": lambda d: d["android-bluetooth-device-extra-rssi"] 
            }
        }
    }

    WIFI_TABLE = {
        "name": "WifiProbe",
        "columns": [
            ("bssid", "TEXT"),
            ("ssid","TEXT"),
            ("level", "INTEGER")
        ]
    }
    
    ANSWER_TABLE = {
        "name": "Answer",
        "columns": [
            ("key", "TEXT PRIMARY KEY"),
            ("value", "TEXT")
        ]
    }
    
    ANSWERLIST_TABLE = {
        "name": "AnswerList",
        "columns": [
            ("key", "TEXT PRIMARY KEY"),
            ("value", "TEXT")
        ]
    }

    DATA_TABLE_LIST = [WIFI_TABLE, BLUETOOTH_TABLE, CALL_LOG_TABLE, SMS_TABLE, ACTIVITY_TABLE, SCREEN_TABLE, LOCATION_TABLE]

    ANSWER_TABLE_LIST = [ANSWER_TABLE, ANSWERLIST_TABLE]

    def getAnswerFromTable(self, key, table):
        #table = "AnswerList" if isinstance(data, list) else "Answer"
        statement = "select key,value from %s" % table
        if key is not None:
            statement = statement + " where key=%s" % key
        c = self.getCursor()
        c.execute(statement, (key,))
        result = c.fetchone()
        return ListWithCount([{ "key": result["key"], "value": ast.literal_eval(result["value"]) }]) if result is not None else None

    def getAnswer(self, key):
        return self.getAnswerFromTable(key, "Answer")

    def getAnswerList(self, key):
        return self.getAnswerFromTable(key, "AnswerList")

    def saveAnswer(self, key, data):
        table = "AnswerList" if isinstance(data, list) else "Answer"
        p = self.getVariablePlaceholder()
        statement = "insert or replace into %s(key, value) values(%s, %s)" %(table,p,p)
        c = self.getCursor()
        c.execute(statement, (key, "%s"%data))
        self.db.commit()
        c.close()
    
    def getData(self, key, startTime, endTime):
        table = key # A simplification for now
        statement = "select '%s' as key,* from %s" %(key,table)
        times = ()

        if startTime is not None or endTime is not None:
            statement += " where "
            if startTime is not None: 
                times = (startTime,)
                statement += "time >= %s" % self.getVariablePlaceholder()
                statement += " and " if endTime is not None else ""
            if endTime is not None:
                times = times + (endTime,)
                statement += "time < %s" % self.getVariablePlaceholder()

        c = self.getCursor()
        c.execute(statement, times)
        return ListWithCount(c.fetchall())
    
    def saveData(self, data):
        # Again, assuming only funf data at the moment...
        tableName = data["key"].rpartition(".")[2]
        source = "funf" if data["key"].rpartition(".")[0].startswith("edu.mit.media.funf") else "sql"
        time = data["time"]
        dataValue = data["value"]
        table = next((t for t in SQLiteInternalDataStore.DATA_TABLE_LIST if tableName.endswith(t["name"])), None)
        if table is None:
            return False
        wildCards = (("%s,"%self.getVariablePlaceholder()) * len(table["columns"]))[:-1]
        columnValues = []
        for columnName in [t[0] for t in table["columns"]]:
            value = time if columnName == "time" else getColumnValueFromRawData(dataValue, columnName, table, source)
            columnValues.append(value)
        statement = "insert into %s(%s) values(%s)" % (table["name"], ",".join([c[0] for c in table["columns"]]), wildCards)
        print statement
        print columnValues
        c = self.getCursor()
        c.execute(statement, tuple(columnValues))
        self.db.commit()
        c.close()

    def getCursor(self):
        raise NotImplementedError("Subclasses must specify how to get a cursor.")

    def getVariablePlaceholder(self):
        raise NotImplementedError("Subclasses must specify a variable placeholder.")

