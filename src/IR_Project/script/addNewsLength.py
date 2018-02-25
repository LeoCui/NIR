#! /usr/bin/env python
#################################################################################
#     File Name           :     addNewsLength.py
#     Created By          :     Leo
#     Creation Date       :     [2018-01-17 19:21]
#     Last Modified       :     [2018-01-17 20:08]
#     Description         :      
#################################################################################

import sys
import json
from lib.utils import *
db = Mysql('localhost', 'root', 'informationRetrieval', 'information_retrieval')
#news_info
tableName = 'news_info'
queryList = list()
queryList.append('id')
conds = ''
results = db.select(tableName, queryList, conds)
for result in results:
    newsId = result[0]
    #content_info
    tableName = 'content_info'
    queryList = list()
    queryList.append('content')
    conds = 'where news_id= ' + str(newsId)
    results = db.select(tableName, queryList, conds)
    newsLength = int(0)
    for result in results:
        content = result[0]
        newsLength += len(content) 
    #update news_info
    tableName = 'news_info'
    extraInfoDict = dict()
    extraInfoDict['news_length'] = newsLength
    extraInfoStr = json.dumps(extraInfoDict)
    print(extraInfoStr)
    sql = 'update news_info set extra_info= ' + '\'' + extraInfoStr + '\'' + ' where id=' + str(newsId)
    print(sql)
    db.update(tableName, sql)
    db.connection.commit()
db.connection.close()

