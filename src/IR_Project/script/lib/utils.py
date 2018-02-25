#! /usr/bin/env python
#################################################################################
#     File Name           :     utils.py
#     Created By          :     Leo
#     Creation Date       :     [2017-12-07 19:44]
#     Last Modified       :     [2018-01-17 19:33]
#     Description         :      
#################################################################################
import re
import sys
import requests
import json
import time
import pymysql
import zlib
import traceback

class Mysql:
    #close
    #rollback
    #commit
    def __init__(self, host, username, password, database):
        self.host = host
        self.username = username
        self.password = password
        self.database = database
        self.connection = pymysql.connect(host, username, password, database, charset='utf8')
        self.cursor = self.connection.cursor()
        
    def select(self, tableName, queryList, conds):
        queryStr = ''
        for query in queryList:
            queryStr = queryStr + query + ','
        queryStr = queryStr[ 0:len(queryStr)-1 ]
        sql = 'select ' + queryStr + ' from  ' + tableName + ' '  + conds;
        self.cursor.execute(sql)
        result = self.cursor.fetchall()
        return result
    
    def insert(self, tableName, valueDict):
        keyStr = ""
        valueStr = ""
        valueList = list()
        for key, value in valueDict.items():
            keyStr += key
            keyStr += ','
            valueStr  += "%s,"
            valueList.append(value)
        keyStr = keyStr[0:len(keyStr)-1]
        valueStr = valueStr[0:len(valueStr)-1]
        sql = "INSERT INTO " + tableName + " (" + keyStr + ") VALUES (" + valueStr + ")" 
        rtn = self.cursor.execute(sql, valueList)
        return self.connection.insert_id()
    
    def update(self, tableName, sql):
        rtn = self.cursor.execute(sql)
        return None
    
    def delete(self):
       return 
