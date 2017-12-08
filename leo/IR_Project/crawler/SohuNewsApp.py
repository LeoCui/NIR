#! /usr/bin/env python
import sys
import requests
import json
import time
import pymysql
import zlib
import traceback
import lib.utils as utils
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
                    r = requests.get(url, params=payload,  headers=headers, timeout = 3)
                    r = r.json()
                    articleList = r['articles']
                except requests.exceptions.ConnectTimeout:
                    traceback.print_exc()
                    break
                except:
                    payload['page'] = payload['page'] + 1
                    traceback.print_exc()
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
    
        
    def getArticle(self, db, articleId, source):
        url = self.articleUrl
        headers = dict()
        payload = dict()
        headers['User-Agent'] = 'NewsApp/29.1 iOS/11.0.3 (iPhone8,1)'
        payload['newsId'] = articleId
        try:
            r = requests.get(url, headers=headers, params=payload, timeout = 3)
            r = r.json()
        except:
            traceback.print_exc()
            return None
        else:
            if 'title' not in r.keys():
                return None
            title = r['title']
            if title == None:
                return None
            webUrl = r['h5link']
            webUrl = utils.formatUrl(webUrl)
            if utils.checkVisited(webUrl, db):
                return -1
            content = r['content']
            content = utils.formatContent(content)
            appUrl = url
            publishTime = r['time']
            news = utils.News(title, appUrl, webUrl, content, publishTime, source)
            return news  

    def getReadCount(self, articleId):
       url = self.readCountUrl
       payload = dict()
       headers = dict()
       headers['User-Agent'] = 'NewsApp/29.1 iOS/11.0.3 (iPhone8,1)'
       payload['newsId'] = articleId
       try:
           r = requests.get(url, params=payload, headers=headers, timeout = 3)
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
            r = requests.get(url, params=payload, headers=headers, timeout = 3)
            r = r.json()
            r = r['response']
            rtn.append(r['allCount'])
            rtn.append(r['favoriteCount'])
        except:
            traceback.print_exc()
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
        while offset < maxCommentCount:
            try:
                r = requests.get(url, params=payload, headers=headers, timeout = 3)
                r = r.json()
            except requests.exceptions.ConnectTimeout:
                traceback.print_exc()
                break
            except:
                payload['page'] = payload['page'] + 1       
                traceback.print_exc()
            else:
                payload['page'] = payload['page'] + 1
                commentList = r['response']['commentList']
                count = len(commentList)
                #print('offset is ' + str(offset))
                #print('count is ' +  str(count))
                if count == 0:
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
                        userName = utils.formatContent(comment['author'])
                        userName = utils.formatComment(userName)
                    else:
                        userName = '匿名用户'
                    content = utils.formatContent(comment['content'])
                    content = utils.formatComment(content)
                    content1 = publishTime + ' ' + userName + ' ' + content
                    commentList1.append(content1)
                offset += count
        return commentList1

    
def main():
    cateUrl = 'https://api.k.sohu.com/api/channel/v5/news.go'
    articleUrl = 'http://api.k.sohu.com/api/news/v5/article.go'
    commentUrl = 'http://api.k.sohu.com/api/comment/getCommentListByCursor.go'
    readCountUrl = 'http://api.k.sohu.com/api/news/article/readQuantity.go'
    db = utils.Mysql('localhost', 'root', 'informationRetrieval', 'information_retrieval')
    source = 'SohuNewsApp'
    sohuAppCrawler = Crawler(cateUrl, articleUrl, commentUrl)
    sohuAppCrawler.readCountUrl = readCountUrl
    cateIdDict = readConf();
    sohuAppCrawler.cateIdDict = cateIdDict
    cateArticleIdDict = sohuAppCrawler.getCateArticleId()
    for cate, articleIdList in cateArticleIdDict.items():
        print('category: ' + cate)
        print('count of article:' + str(len(articleIdList)))
        number = 1
        duplicateCount = 0
        failCount = 0
        for articleId in articleIdList:
            if number % 50 == 0:
                print("handle  " + str(number) + '    duplicateCount: ' + str(duplicateCount) + '   failCount:  '  + str(failCount))
            number += 1
            news = sohuAppCrawler.getArticle(db, articleId, source)
            if news == None:
                failCount += 1
                continue
            if news == -1:
                duplicateCount += 1
                continue
            readCount = sohuAppCrawler.getReadCount(articleId)
            news.readCount = readCount
            list1 = sohuAppCrawler.getComAndFavCount(articleId)
            news.commentCount = list1[0]
            news.upCount = list1[1]
            commentList = sohuAppCrawler.getComment(articleId, min(100, news.commentCount))
            news.category = cate
            news.commentList = commentList
            utils.storeToDb(news, db)
    db.connection.close()

def readConf():
    cateIdDict = dict()
    
    cateIdDict['international'] = (45, 2000)
    cateIdDict['society'] = (23, 2000)
    cateIdDict['technology'] = (6, 2000)
    cateIdDict['finance'] = (4,2000)
    cateIdDict['sport'] = (2, 2000)
    cateIdDict['military'] = (5, 2000)
    cateIdDict['entertainment'] = (3, 2000)
    cateIdDict['beijing'] = (283, 2000)
    return cateIdDict
if __name__ == '__main__':
    main()
