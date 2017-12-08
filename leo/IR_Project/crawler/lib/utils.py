#! /usr/bin/env python
#################################################################################
#     File Name           :     utils.py
#     Created By          :     Leo
#     Creation Date       :     [2017-12-07 19:44]
#     Last Modified       :     [2017-12-07 23:27]
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
def formatContent(str1):
    if str1 == None:
        return None
    str1 = str1.replace('&nbsp','')
    reObj = re.compile(r'<[^>]+>')
    str1 = reObj.sub('', str1)
    reObj = re.compile(r'\[[^\]]+\]')
    str1 = reObj.sub('',str1)
    reObj = re.compile(r'[\s\u3000]')
    str1 = reObj.sub('', str1)
    return str1

# &amp; to &
def formatUrl(url):
    if url == None:
        return None
    url = url.replace('&amp;','&')
    return url


#remove '|'  from userName and content
def formatComment(str1):
    if str1 == None:
        return None
    str1 = str1.replace('|','')
    return str1


class News:
    def __init__(self, title, appUrl, webUrl, content, publishTime, source):
        self.title = title
        self.appUrl = appUrl
        self.category = ''
        self.webUrl = webUrl
        self.content = content
        self.source = source
        self.commentList = list()
        self.readCount = -1
        self.commentCount = -1
        self.upCount = -1
        self.downCount = -1
        self.publishTime = publishTime

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
        sql = 'select ' + queryStr + ' from  ' + tableName + ' where ' + conds;
        self.cursor.execute(sql)
        result = self.cursor.fetchone()
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
        #print(sql)
        #print(valueList)
        self.cursor.execute(sql, valueList)
        return self.connection.insert_id()
    
    def update(self):
        return
    
    def delete(self):
        return 
    
def storeToDb(news, db):
    try:
        #news_info
        valueDict = dict()
        valueDict['title'] = news.title
        valueDict['url'] = news.webUrl
        valueDict['source'] = news.source
        valueDict['url_hash'] = zlib.crc32(bytes(news.webUrl,'utf8'))
        valueDict['pv'] = news.readCount
        valueDict['comment_number'] = news.commentCount
        if news.publishTime != '':
            valueDict['publish_time'] = news.publishTime
        valueDict['category'] = news.category
        newsId = db.insert('news_info', valueDict)
        #content_info
        content = news.content
        len1 = len(content)
        offset = 0
        strSize = 340
        maxByteSize = 1024
        i = 0
        while offset < len1:
            #print(offset)
            #print(offset+strSize)
            str = content[offset : offset + strSize]
            str1 = str.encode(encoding = 'utf8')
            if len(str1) > maxByteSize:
                str = content[offset, offset + strSize/2]
                str1 = str.encode(encoding = 'utf8')
                offset = offset - strSize/2
            valueDict = dict()
            valueDict['news_id'] = newsId
            valueDict['sequence_number'] = i
            valueDict['content'] = str
            db.insert('content_info', valueDict)
            offset = offset + strSize
            i = i + 1
        #comment_info
        commentList = news.commentList
        str1 = ''
        count = 0
        for comment in commentList:
            temp = str1 + comment + '|'
            temp = temp.encode(encoding = 'utf8')
            if len(temp) > maxByteSize:
                valueDict = dict()
                valueDict['news_id'] = newsId
                valueDict['comment_number'] = count        
                valueDict['content'] = str1
                db.insert('comment_info', valueDict)
                str1 = ''
                count = 0
            else:
                str1 = str1 + comment + '|'
                count += 1
        if count > 0:
            valueDict = dict()
            valueDict['news_id'] = newsId
            valueDict['comment_number'] = count
            valueDict['content'] = str1
            db.insert('comment_info', valueDict)
    except: 
        traceback.print_exc()
        print(valueDict)
        db.connection.rollback()
    else:
        db.connection.commit()

def checkVisited(url, db):
    if url == None:
        return False
    urlHash = zlib.crc32(bytes(url,'utf8'))
    queryList = ['url']
    conds = 'url_hash=' + str(urlHash)
    urlList = db.select('news_info', queryList, conds);
    if urlList is None:
        return False
    for url1 in urlList:
        if url == url1:
            return True
    return False

