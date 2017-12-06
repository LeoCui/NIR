#! /usr/bin/env python
import sys
import requests
import json
import time
import pymysql
import zlib
import traceback

class Crawler:
    def __init__(self, cateUrl, articleUrl, commentUrl):
        self.cateUrl = cateUrl
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
            payload['channelId'] = value[0] 
            payload['num'] = 20
            payload['page'] = 1
            maxArticleCount = value[1]
            url = self.cateUrl
            flag = False
            while True:
                try:
                    r = requests.get(url, params=payload,  headers=headers)
                    r = r.json()
                    articleList = r['articles']
                except:
                    traceback.print_exc()
                    break
                else:
                    payload['page'] = payload['page'] + 1
                    print('get article: ' + str(len(articleList)))
                    if len(articleList) == 0:
                        break
                    for article in articleList:
                        if 'newsId' not in article.keys():
                            continue
                        newsId = article['newsId']
                        # 视频过滤掉 todo
                        if article['newsType'] != 3:
                            continue
                        articleIdSet.add(newsId)
                        if len(articleIdSet) >= maxArticleCount:
                            flag = True
                            break
                    if flag == True:
                        break
            cateArticleIdDict[cate] = articleIdSet
        return cateArticleIdDict
    
        
    def getArticle(self, articleId):
        url = self.articleUrl
        headers = dict()
        payload = dict()
        headers['User-Agent'] = 'NewsApp/29.1 iOS/11.0.3 (iPhone8,1)'
        payload['newsId'] = articleId
        try:
            r = requests.get(url, headers=headers, params=payload)
            r = r.json()
        except:
            traceback.print_exc()
            return None
        else:
            title = r['title']
            if title == None:
                return None
            content = r['content']
            content = self.deleteTag(content)
            appUrl = url
            webUrl = r['h5link']
            webUrl = self.formatUrl(webUrl)
            print(webUrl)
            publishTime = r['time']
            news = News(title, appUrl, webUrl, content, publishTime)
            return news  

    def getReadCount(self, articleId):
       url = self.readCountUrl
       payload = dict()
       headers = dict()
       headers['User-Agent'] = 'NewsApp/29.1 iOS/11.0.3 (iPhone8,1)'
       payload['newsId'] = articleId
       try:
           r = requests.get(url, params=payload, headers=headers)
           r = r.json()
       except:
           traceback.print_exc()
           return -1
       else:
           return r['readQuantity']

    def getComAndFavCount(self, articleId):
        url = self.commentUrl
        payload = dict()
        headers = dict()
        headers['User-Agent'] = 'NewsApp/29.1 iOS/11.0.3 (iPhone8,1)'
        payload['busiCode'] = 2
        payload['id'] = articleId
        payload['page'] = 1
        payload['rollType'] = 2
        payload['size'] = 10
        payload['type'] = 3
        rtn = list()
        try:
            r = requests.get(url, params=payload, headers=headers)
            r = r.json()
            r = r['response']
            rtn.append(r['allCount'])
            rtn.append(r['favoriteCount'])
        except:
            traceback.print_exc()
            print(r)
            rtn.append(-1)
            rtn.append(-1)
        return rtn

    def getComment(self, articleId, maxCommentCount):
        url = self.commentUrl
        payload = dict()
        headers = dict()
        headers['User-Agent'] = 'NewsApp/29.1 iOS/11.0.3 (iPhone8,1)'
        payload['busiCode'] = 2
        payload['id'] = articleId
        payload['page'] = 1
        payload['rollType'] = 2
        payload['size'] = 10
        payload['type'] = 3
        commentList1 = list()
        offset = 0
        retryTime = 0
        maxRetryTime = 5
        while offset < maxCommentCount:
            try:
                r = requests.get(url, params=payload, headers=headers)
                r = r.json()
            except:
                traceback.print_exc()
                break
            else:
                payload['page'] = payload['page'] + 1
                commentList = r['response']['commentList']
                count = len(commentList)
                #print('offset is ' + str(offset))
                #print('count is ' +  str(count))
                if count == 0:
                    retryTime += 1
                if retryTime >= maxRetryTime:
                    break
                for comment in commentList:
                    if 'ctime' in comment.keys():
                        publishTime = comment['ctime']
                        publishTime = int(publishTime) / 1000
                        publishTime = time.localtime(publishTime)
                        publishTime = time.strftime("%Y-%m-%d %H:%M:%S",publishTime)
                    else:
                        publishTime = '0000-00-00 00:00:00'
                    if 'author' in comment.keys() and comment['author']!=None:
                        userName = self.formatComment(comment['author'])
                    else:
                        userName = '匿名用户'
                    content = self.deleteTag(comment['content'])
                    content = self.formatComment(content)
                    content1 = publishTime + ' ' + userName + ' ' + content
                    commentList1.append(content1)
                offset += count
        return commentList1
    
    def deleteTag(self, str):
        if str == None:
            return None
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
            if str[i] == '|' or str[i] == ' ' or str[i] == '\n' or str[i] == '\t' or str[i] == '\r':
                continue
            str1 += str[i]
        return str1
    
    def storeToDb(self, news, db):
        try:
            #news_info
            print(news.webUrl)
            if self.checkVisited(news.webUrl, db):
                print("duplicate news")
                return 
            valueDict = dict()
            valueDict['title'] = news.title
            valueDict['url'] = news.webUrl
            valueDict['source'] = 'SohuNewsApp'
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
    cateUrl = 'https://api.k.sohu.com/api/channel/v5/news.go'
    articleUrl = 'http://api.k.sohu.com/api/news/v5/article.go'
    commentUrl = 'http://api.k.sohu.com/api/comment/getCommentListByCursor.go'
    readCountUrl = 'http://api.k.sohu.com/api/news/article/readQuantity.go'
    db = Mysql('localhost', 'root', '123456', 'information_retrieval')
    sohuAppCrawler = Crawler(cateUrl, articleUrl, commentUrl)
    sohuAppCrawler.readCountUrl = readCountUrl
    cateIdDict = readConf();
    sohuAppCrawler.cateIdDict = cateIdDict
    cateArticleIdDict = sohuAppCrawler.getCateArticleId()
    for cate, articleIdList in cateArticleIdDict.items():
        print('category: ' + cate)
        print('count of article:' + str(len(articleIdList)))
        number = 0
        for articleId in articleIdList:
            print("handle  " + str(number) + ':' + str(articleId))
            news = sohuAppCrawler.getArticle(articleId)
            if news == None:
                continue
            #网易的锅，无法显示全部评论
            readCount = sohuAppCrawler.getReadCount(articleId)
            news.readCount = readCount
            list1 = sohuAppCrawler.getComAndFavCount(articleId)
            news.commentCount = list1[0]
            news.upCount = list1[1]
            commentList = sohuAppCrawler.getComment(articleId, min(100, news.commentCount))
            news.category = cate
            news.commentList = commentList
            sohuAppCrawler.storeToDb(news, db)
            number += 1
    db.connection.close()

def readConf():
    cateIdDict = dict()
    #cateIdDict['international'] = (45, 500)
    #cateIdDict['society'] = (23, 1000)
    cateIdDict['technology'] = (6, 500)
    #cateIdDict['finance'] = (4, 500)
    cateIdDict['sport'] = (2, 500)
    #cateIdDict['military'] = (5, 500)
    cateIdDict['entertainment'] = (3, 500)
    cateIdDict['beijing'] = (283, 50)
    return cateIdDict
if __name__ == '__main__':
    main()
