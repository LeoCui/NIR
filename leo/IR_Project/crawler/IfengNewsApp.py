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
        
    def getCateNews(self):
        cateNewsDict = dict()
        payload = dict()
        headers = dict()
        headers['User-Agent'] = 'NewsApp/29.1 iOS/11.0.3 (iPhone8,1)'
        for cate,value in self.cateIdDict.items():
            newsList = list()
            offset = 0
            payload['id'] = value[0] 
            payload['page'] = 1
            maxArticleCount = value[1]
            url = self.cateUrl
            flag = False
            while True:
                try:
                    r = requests.get(url, params=payload,  headers=headers)
                    r = r.json() 
                    articleList = r[0]['item']
                except:
                    traceback.print_exc()
                    break
                else:
                    payload['page'] = payload['page'] + 1
                    print('get article count: ' + str(len(articleList)))
                    if len(articleList) == 0:
                        break
                    for article in articleList:
                        if 'id' not in article.keys():
                            continue
                        if 'type' not in article.keys() or article['type'] != 'doc':
                            continue
                        news = dict()
                        news['articleId'] = article['id']
                        news['commentUrl'] = article['commentsUrl']
                        news['commentNum'] = article['comments']
                        newsList.append(news)
                        if len(newsList) >= maxArticleCount:
                            flag = True
                            break
                    if flag == True:
                        break
            cateNewsDict[cate] = newsList
        return cateNewsDict
    
        
    def getArticle(self, articleId):
        url = self.articleUrl
        url += articleId
        headers = dict()
        payload = dict()
        headers['User-Agent'] = 'NewsApp/29.1 iOS/11.0.3 (iPhone8,1)'
        try:
            r = requests.get(url, headers=headers, params=payload)
            r = r.json()
        except:
            traceback.print_exc()
            return None
        else:
            r = r['body']
            title = r['title']
            if title == None:
                return None
            content = r['text']
            content = self.deleteTag(content)
            appUrl = url
            webUrl = r['shareurl']
            webUrl = self.formatUrl(webUrl)
            publishTime = r['updateTime']
            news = News(title, appUrl, webUrl, content, publishTime) 
            return news  


    def getComment(self, articleId, maxCommentCount):
        url = self.commentUrl
        payload = dict()
        headers = dict()
        headers['User-Agent'] = 'NewsApp/29.1 iOS/11.0.3 (iPhone8,1)'
        payload['limit'] = 20
        payload['page'] = 1
        payload['comments_url'] = articleId
        commentList1 = list()
        offset = 0
        retryTime = 0
        maxRetryTime = 5
        while offset < maxCommentCount:
            try:
                r = requests.get(url, params=payload, headers=headers)
                r = r.json()
                commentList = r['data']
            except:
                traceback.print_exc()
                break
            else:
                payload['page'] = payload['page'] + 1
                count = len(commentList)
                #print('offset is ' + str(offset))
                #print('count is ' +  str(count))
                if count == 0:
                    retryTime += 1
                if retryTime >= maxRetryTime:
                    break
                for comment in commentList:
                    if 'add_time' in comment['data'].keys():
                        publishTime = int(comment['data']['add_time'])
                        publishTime = time.localtime(publishTime)
                        publishTime = time.strftime("%Y-%m-%d %H:%M:%S",publishTime)
                    else:
                        publishTime = '0000-00-00 00:00:00'
                    if 'nickname' in comment.keys() and comment['nickname']!=None:
                        userName = self.formatComment(comment['nickname'])
                    else:
                        userName = '匿名用户'
                    content = self.deleteTag(comment['data']['comment_contents'])
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
            if self.checkVisited(news.webUrl, db):
                print("duplicate news")
                return 
            valueDict = dict()
            valueDict['title'] = news.title
            valueDict['url'] = news.webUrl
            valueDict['source'] = 'IfengNewsApp'
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
    cateUrl = 'https://api.iclient.ifeng.com/ClientNews'
    articleUrl = ''
    commentUrl = 'https://user.iclient.ifeng.com/Social_Api_Comment/getCommentList'
    db = Mysql('localhost', 'root', '123456', 'information_retrieval')
    ifengAppCrawler = Crawler(cateUrl, articleUrl, commentUrl)
    cateIdDict = readConf();
    ifengAppCrawler.cateIdDict = cateIdDict
    cateNewsDict = ifengAppCrawler.getCateNews()
    for cate, newsList in cateNewsDict.items():
        print('category: ' + cate)
        print('count of article:' + str(len(newsList)))
        number = 0
        for news in newsList:
            articleId = news['articleId']
            commentUrl = news['commentUrl']
            commentNum = news['commentNum']
            print("handle  " + str(number) + ':' + str(articleId))
            news = ifengAppCrawler.getArticle(articleId)
            if news == None:
                continue
            news.commentCount = commentNum
            commentList = ifengAppCrawler.getComment(commentUrl, min(100, int(news.commentCount)))
            news.category = cate
            news.commentList = commentList
            ifengAppCrawler.storeToDb(news, db)
            number += 1
    db.connection.close()

def readConf():
    cateIdDict = dict()
    cateIdDict['society'] = ('NXWPD,FOCUSNXWPD', 500)
    cateIdDict['technology'] = ('KJ123,FOCUSKJ123', 500)
    cateIdDict['finance'] = ('CJ33,FOCUSCJ33,HNCJ33', 500)
    cateIdDict['sport'] = ('TY43,FOCUSTY43,TYLIVE', 500)
    cateIdDict['military'] = ('JS83,FOCUSJS83', 500)
    cateIdDict['entertainment'] = ('YL53,FOCUSYL53', 500)
    cateIdDict['nba'] = ('NXWPD,FOCUSNXWPD', 50)
    cateIdDict['politics'] = ('SZPD,FOCUSSZPD', 500)
    return cateIdDict
if __name__ == '__main__':
    main()
