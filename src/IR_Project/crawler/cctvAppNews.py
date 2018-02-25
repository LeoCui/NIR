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
            payload['id'] = value[0] 
            payload['n'] = 20
            payload['p'] = 1
            maxArticleCount = value[1]
            url = self.cateUrl
            flag = False
            while True:
                try:
                    r = requests.get(url, params=payload,  headers=headers, timeout=3)
                    r = r.json()
                    articleList = r['itemList']
                except requests.exceptions.ConnectTimeout:
                    traceback.print_exc()
                    break
                except:
                    payload['p'] = payload['p'] + 1
                    traceback.print_exc()
                else:
                    payload['p'] = payload['p'] + 1
                    print('get article: ' + str(len(articleList)))
                    if len(articleList) == 0:
                        break
                    for article in articleList:
                        if 'itemID' not in article.keys():
                            continue
                        newsId = article['itemID']
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
        payload['id'] = articleId
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
            webUrl = r['url']
            webUrl = utils.formatUrl(webUrl)
            if utils.checkVisited(webUrl, db):
                return -1
            content = r['content']
            content = utils.formatContent(content)
            appUrl = url
            publishTime = r['pubtime']
            news = utils.News(title, appUrl, webUrl, content, publishTime, source)
            return news  
    
    def getCommentCount(self, articleId):
        url = self.commentUrl 
        payload = dict()
        headers = dict()
        headers['User-Agent'] = 'NewsApp/29.1 iOS/11.0.3 (iPhone8,1)'
        payload['itemid'] = articleId
        payload['page'] = 1
        payload['prepare'] = 20
        payload['app'] = 'news'
        try:
            r = requests.get(url, params=payload, headers=headers, timeout=3)
            r = r.json()
            commentCount = r['data']['total']
        except:
            traceback.print_exc()
            return -1
        return commentCount

    def getComment(self, articleId, maxCommentCount):
        url = self.commentUrl
        payload = dict()
        headers = dict()
        headers['User-Agent'] = 'NewsApp/29.1 iOS/11.0.3 (iPhone8,1)'
        payload['itemid'] = articleId
        payload['page'] = 1
        payload['prepare'] = 20
        payload['app'] = 'news'
        commentList1 = list()
        offset = 0
        while offset < maxCommentCount:
            try:
                r = requests.get(url, params=payload, headers=headers, timeout=3)
                r = r.json()
                commentList = r['data']['content']
            except requests.exceptions.ConnectTimeout:
                traceback.print_exc()
                break
            except:
                payload['page'] = payload['page'] + 1
                traceback.print_exc()
            else:
                payload['page'] = payload['page'] + 1
                count = len(commentList)
                if count == 0:
                    break
                for key,comment in commentList.items():
                    if 'dateline' in comment.keys():
                        publishTime = comment['dateline']
                        publishTime = time.localtime(int(publishTime))
                        publishTime = time.strftime("%Y-%m-%d %H:%M:%S",publishTime)
                    else:
                        publishTime = '0000-00-00 00:00:00'
                    if 'author' in comment.keys() and comment['author']!=None:
                        userName = utils.formatComment(comment['author'])
                        userName = utils.formatComment(userName)
                    else:
                        userName = '匿名用户'
                    content = utils.formatContent(comment['message'])
                    content = utils.formatComment(content)
                    content1 = publishTime + ' ' + userName + ' ' + content
                    commentList1.append(content1)
                offset += count
        return commentList1
    
         
def main():
    cateUrl = 'http://api.cportal.cctv.com/api/rest/navListInfo/getHandDataListInfoNew'
    articleUrl = 'http://api.cportal.cctv.com/api/rest/articleInfo'
    commentUrl = 'http://newcomment.cntv.cn/comment/list'
    db = utils.Mysql('localhost', 'root', 'informationRetrieval', 'information_retrieval')
    source = 'cctvNewsApp'
    cctvAppCrawler = Crawler(cateUrl, articleUrl, commentUrl)
    cateIdDict = readConf();
    cctvAppCrawler.cateIdDict = cateIdDict
    cateArticleIdDict = cctvAppCrawler.getCateArticleId()
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
            time1 = time.time()
            news = cctvAppCrawler.getArticle(db, articleId, source)
            time2 = time.time()
            #print("getArticle: " + str(time2-time1))
            if news == None:
                failCount += 1
                continue
            if news == -1:
                duplicateCount += 1
                continue
            commentCount = cctvAppCrawler.getCommentCount(articleId)
            news.commentCount = commentCount
            commentList = cctvAppCrawler.getComment(articleId, min(int(commentCount), 100))
            time3 = time.time()
            #print("getComment: " + str(time3-time2))
            news.category = cate
            news.commentList = commentList
            utils.storeToDb(news, db)
            time4 = time.time()
            #print("store to db "  + str(time4-time3))
    db.connection.close()

def readConf():
    cateIdDict = dict()
    cateIdDict['international'] = ('Nav-iqwRTtNj4tQCEkyUkBzW160812', 2000)
    cateIdDict['society'] = ('Nav-GxfrDirK3AR2nnyMC9Ub160812', 2000)
    cateIdDict['technology'] = ('Nav-ZzGRAcda1ZRF2a2M05n9170412', 2000)
    cateIdDict['finance'] = ('Nav-Y7GOiDYMu0PLMSWBFJRs160812', 2000)
    cateIdDict['sport'] = ('Nav-D7N9jNkwGwLX5tIo7vSF161101', 2000)
    cateIdDict['military'] = ('Nav-c9aZErstPWnzhTy9ZHTB160812', 2000)
    cateIdDict['hotNews'] = ('Nav-9Nwml0dIB6wAxgd9EfZA160510', 2000)
    cateIdDict['beijing'] = ('Nav-JEZssQyzruNBOB1rn9W1170321', 2000)
    cateIdDict['politics'] = ('Nav-x1EttmgGbITPUk4msBDj160812', 2000)
    cateIdDict['taiwan'] = ('Nav-uMt97G2SKGTYfI89PynH160812', 2000)  
    return cateIdDict
if __name__ == '__main__':
    main()
