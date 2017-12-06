#! /usr/bin/env python
import sys
import requests
import json
import time
import pymysql
import zlib
import traceback

class Crawler:
    def __init__(self, cateUrl1, cateUrl2, articleUrl, commentUrl):
        self.cateUrl1 = cateUrl1
        self.cateUrl2 = cateUrl2
        self.articleUrl = articleUrl
        self.commentUrl = commentUrl
        self.specialNewsUrl = ''
        self.cateIdDict = dict()
        
    def getCateArticleId(self):
        cateArticleIdDict = dict()
        payload = dict()
        headers = dict()
        headers['User-Agent'] = 'NewsApp/29.1 iOS/11.0.3 (iPhone8,1)'
        for cate,value in self.cateIdDict.items():
            articleIdSet = set()
            offset = 0
            maxArticleCount = value[2]
            kind = value[0]
            if kind == 1: 
                payload['from'] = value[1] 
                payload['devId'] = 'QMEYFEbZjK7S8W7Xdz5ujdKsWvHlCU3m%2FH219JXxZvNqutd1gfNLYc4u8crYIMhg'
                payload['version'] = '29.1'
                payload['spever'] = 'false'
                payload['net'] = 'wifi'
                payload['lat'] = 'HvUousyew2kGvXTue4Km4g%3D%3D'
                payload['lon'] = 'XOnRjaxTRwGS%2BzjmlZJgTw%3D%3D'
                payload['ts'] = '1511969424'
                payload['sign'] = '6pEXLh37vd9wsIT4TLJMJ5LXikaXFqvcbuadPy7+tnd48ErR02zJ6/KXOnxX046I'
                payload['encryption'] = 1
                payload['canal'] = 'appstore'
                payload['offset'] = offset
                payload['size'] = 10
                payload['fn'] = 2
                url = self.cateUrl2
                offset = 10
            flag = False
            while True:
                if kind == 0:
                    url = self.cateUrl1 + value[1] + '/' + str(offset) + '-20.html'
                    offset = offset + 20
                if kind == 1:
                    payload['offset'] = offset
                    offset = offset + 0
                #print(url)
                try:
                    r = requests.get(url, params=payload,  headers=headers)
                    r = r.json()
                except:
                    traceback.print_exc()
                    break
                else:
                    for key,articleList in r.items():
                        temp = len(articleList)
                        if temp == 0:
                            flag = True
                            break
                        print("get " + str(temp) + ' article')
                        for article in articleList:
                            if 'docid' not in article.keys():
                                continue
                            docId = article['docid']
                            # 视频过滤掉
                            if 'videoID' in article.keys():
                                continue
                            # 如果是专题的话
                            if 'specialID' in article.keys():
                                specialId = article['specialID']
                                specialArticleIdSet = self.getSpecialArticleId(specialId) 
                                if len(articleIdSet.union(specialArticleIdSet)) >= maxArticleCount:
                                    flag = True
                                    break
                                articleIdSet = articleIdSet.union(specialArticleIdSet)
                            else:
                                articleIdSet.add(docId)
                                if(len(articleIdSet) >= maxArticleCount):
                                    flag = True
                                    break
                        break
                    if flag == True:
                        cateArticleIdDict[cate] = articleIdSet
                        break
        return cateArticleIdDict
    
    def getSpecialArticleId(self, specialId):
        url = self.specialNewsUrl + specialId + '.html'
        headers = dict()
        headers['User-Agent'] = 'NewsApp/29.1 iOS/11.0.3 (iPhone8,1)'
        r = requests.get(url, headers=headers)
        try:
            r = requests.get(url, headers=headers)
            r = r.json()
        except:
            traceback.print_exc()
        else:
            docIdSet = set()
            topicList = r[specialId]['topics']
            for topic in topicList:
                docList = topic['docs']
                for doc in docList:
                    docId = doc['docid']
                    docIdSet.add(docId)
            #print('docIdSet: ')
            #print(docIdSet)
            return docIdSet
        
    def getArticle(self, articleId):
        #print('getArticle')
        url = self.articleUrl + articleId  + '/full.html'
        #print(url)
        headers = dict()
        headers['User-Agent'] = 'NewsApp/29.1 iOS/11.0.3 (iPhone8,1)'
        try:
            r = requests.get(url, headers=headers)
            r = r.json()
        except:
            traceback.print_exc()
            return None
        else:
            r = r[articleId]
            title = r['title']
            content = r['body']
            content = self.deleteTag(content)
            appUrl = url
            webUrl = r['shareLink']
            webUrl = self.formatUrl(webUrl)
            commentCount = r['replyCount']
            upCount = r['threadVote']
            downCount = r['threadAgainst']
            publishTime = r['ptime']
            news = News(title, appUrl, webUrl, content, publishTime)
            news.commentCount = commentCount
            news.upCount = upCount
            news.downCount = downCount
            return news  
    
    def getComment(self, articleId, maxCommentCount):
        url = self.commentUrl + articleId + '/app/comments/newList'
        payload = dict()
        headers = dict()
        headers['User-Agent'] = 'NewsApp/29.1 iOS/11.0.3 (iPhone8,1)'
        Limit = 10
        payload['format'] = 'building'
        payload['ibc'] = 'newsappios'
        payload['headLimit'] = 2
        payload['tailLimit'] = 3 
        payload['showLevelThreshold'] = 5
        payload['limit'] = Limit
        offset = 0
        commentList = list()
        retryTime = 0
        maxRetryTime = 5
        while offset < maxCommentCount:
            payload['offset'] = offset
            #print(url)
            try:
                r = requests.get(url, params=payload, headers=headers)
                r = r.json()
            except:
                offset += (Limit + payload['headLimit'] + payload['tailLimit'])
                traceback.print_exc()
            else:
                commentDict = r['comments']
                count = len(commentDict)
                #print('offset is ' + str(offset))
                #print('count is ' +  str(count))
                if count == 0:
                    retryTime += 1
                if retryTime >= maxRetryTime:
                    break
                for id,comment in commentDict.items():
                    if 'createTime' in comment.keys():
                        publishTime = comment['createTime']
                    else:
                        publishTime = '0000-00-00 00:00:00'
                    if 'nickName' in comment['user'].keys() and comment['user']['nickname']!=None:
                        userName = self.formatComment(comment['user']['nickname'])
                    else:
                        userName = '匿名用户'
                    content = self.deleteTag(comment['content'])
                    content = self.formatComment(content)
                    content1 = publishTime + ' ' + userName + ' ' + content
                    commentList.append(content1)
                offset += count
        return commentList
    
    def deleteTag(self, str):
        len1 = len(str)
        str1 = ''
        i = 0
        flag = 0
        for i in range(0,len1):
            if str[i]=='<':
                flag = 1
            if str[i]=='>':
                flag = 0
            if flag == 1 or str[i]=='>' or str[i]=='\u3000':
                continue
            str1 += str[i]
        return str1

    # &amp; to &
    def formatUrl(self, url):
        if url == None:
            return None
        len1 = len(url)
        url1 = ''
        i = 0
        while i < len1:
            url1 += url[i]
            if url[i] == '&' and url[i+1] == 'a' and url[i+2] == 'm' and url[i+3] == 'p' and url[i+4] ==';':
                i = i + 4
            i = i + 1
        return url1

    #remove '|' and ' ' from userName and content
    def formatComment(self, str):
        len1 = len(str)
        str1 = ''
        i = 0
        for i in range(0,len1):
            if str[i] == '|' or str[i] == ' ' or str[i] == '\t' or str[i] == '\r' or str[i] == '\n':
                continue
            str1 += str[i]
        return str1
    
    def storeToDb(self, news, db):
        try:
            #news_info
            if self.checkVisited(news.webUrl, db):
                print("duplicate news")
                return 
            valueDict = dict()
            valueDict['title'] = news.title
            valueDict['url'] = news.webUrl
            valueDict['source'] = 'NeteaseNewsApp'
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

    def checkVisited(self, url, db):
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

class News:
    def __init__(self, title, appUrl, webUrl, content, publishTime):
        self.title = title
        self.appUrl = appUrl
        self.category = ''
        self.webUrl = webUrl
        self.content = content
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
    
    
def main():
    articleUrl = 'https://c.m.163.com/nc/article/'
    commentUrl = 'https://comment.api.163.com/api/v1/products/a2869674571f77b5a0867c3d71db5856/threads/'
    cateUrl1 = 'https://c.m.163.com/nc/article/list/'
    cateUrl2 = 'https://c.m.163.com/dlist/article/dynamic'
    specialNewsUrl = 'https://c.m.163.com/nc/special/'
    db = Mysql('localhost', 'root', '123456', 'information_retrieval')
    neteaseAppCrawler = Crawler(cateUrl1, cateUrl2, articleUrl, commentUrl)
    neteaseAppCrawler.specialNewsUrl = specialNewsUrl
    cateIdDict = readConf();
    neteaseAppCrawler.cateIdDict = cateIdDict
    cateArticleIdDict = neteaseAppCrawler.getCateArticleId()
    for cate, articleIdList in cateArticleIdDict.items():
        print('category: ' + cate)
        print('count of article:' + str(len(articleIdList)))
        number = 0
        for articleId in articleIdList:
            print("handle  " + str(number))
            news = neteaseAppCrawler.getArticle(articleId)
            if news == None:
                continue
            #网易的锅，无法显示全部评论
            commentList = neteaseAppCrawler.getComment(articleId, min(news.commentCount, 100))
            news.category = cate
            news.commentList = commentList
            neteaseAppCrawler.storeToDb(news, db)
            number += 1
    db.connection.close()

def readConf():
    cateIdDict = dict()
    cateIdDict['politics'] = (0, 'T1414142214384', 500)
    cateIdDict['society'] = (1, 'T1348648037603', 500)
    cateIdDict['technology'] = (1, 'T1348649580692', 300)
    cateIdDict['finance'] = (1, 'T1348648756099', 300)
    cateIdDict['sport'] = (1, 'T1348649079062', 300)
    cateIdDict['military'] = (1, 'T1348648141035', 300)
    cateIdDict['entertainment'] = (1, 'T1348648517839', 300)
    cateIdDict['NBA'] = (1, 'T1348649145984', 300)
    return cateIdDict
if __name__ == '__main__':
    main()
