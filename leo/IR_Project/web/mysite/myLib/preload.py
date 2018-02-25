#! /usr/bin/env python
import sys
import json
import numpy
sys.path.append('/Users/Leo/Documents/github/NIR/leo/IR_Project/web/mysite/')
import myLib.utils as utils
class Preload:
    db = None
    postingList = dict()
    stopWordList = list()
    newsLengthDict = dict()
    docCount = 0
    newsAvgLength = 0
    stopWordPath = '/Users/Leo/Documents/github/NIR/leo/IR_Project/web/mysite/myLib/stopWord.txt'
    def init(self):
        db = utils.Mysql('localhost','root','informationRetrieval','information_retrieval')
        stopWordList = self.getStopWordList()
        postingList = self.getPostingList(db)
        docCount = self.getDocCount(db)
        newsLengthDict = self.getNewsLengthDict(db)
        Preload.db = db
        Preload.stopWordList = stopWordList
        Preload.postingList = postingList
        Preload.docCount = docCount
        Preload.newsLengthDict = newsLengthDict
        Preload.newsAvgLength = self.averageLength(newsLengthDict)
        
        print(Preload.newsAvgLength)

    def averageLength(self, lengthDict):
        length = []
        for item in lengthDict.items():
            length.append(item[1])
        return numpy.mean(length)

    def getNewsLengthDict(self, db):
        tableName = 'news_info'
        queryList = list()
        queryList.append('id')
        queryList.append('extra_info')
        conds = ''
        results = db.select(tableName, queryList, conds)
        newsLengthDict = dict()
        for result in results:
            newsId = result[0]
            extraInfoStr = result[1]
            extraInfoDict = json.loads(extraInfoStr)
            length = extraInfoDict['news_length']
            newsLengthDict[newsId] = length
        return newsLengthDict

    def getStopWordList(self):
        stopWordList = list()
        with open(Preload.stopWordPath, 'r') as f:
            for line in f.readlines():
                stopWordList.append(line)
        return stopWordList
    def getPostingList(self, db):
        tableName = 'posting_list'
        queryList = list()
        queryList.append('term')
        queryList.append('content')
        conds = ''
        results = db.select(tableName, queryList, conds)
        postingList = dict()
        if results != None:
            for result in results:
                term = result[0]
                content = result[1]
                if term not in postingList.keys():
                    postingListValue = dict()
                    postingListValue['docDict'] = self.parseContent(content)
                    postingList[term] = postingListValue
                else:
                    postingList[term]['docDict'].update( self.parseContent(content))
                postingList[term]['df'] = len(postingList[term]['docDict'])
        return postingList
    
    def parseContent(self, content):
        docs = content.split('|')
        docDict = dict()
        if docs != None:
            for doc in docs:
                results = doc.split(' ')
                newsId = results[1]
                tf = results[2]
                docDict[newsId] = tf
        return docDict

    def getDocCount(self, db):
        tableName = 'news_info'
        queryList = list()
        queryList.append('count(*)')
        conds = ''
        count = 0
        results = db.select(tableName, queryList, conds)
        if results != None and len(results)>0:
            count = results[0][0]
        return count 
