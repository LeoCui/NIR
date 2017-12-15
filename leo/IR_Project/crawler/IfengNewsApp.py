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
                    r = requests.get(url, params=payload,  headers=headers, timeout = 3)
                    r = r.json() 
                except requests.exceptions.ConnectTimeout:
                    traceback.print_exc()
                    break
                except:
                    payload['page'] = payload['page'] + 1
                    traceback.print_exc()
                else:
                    if len(r) > 0 and 'item' in r[0].keys():
                        articleList = r[0]['item']
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
    
        
    def getArticle(self, db, articleId, source):
        url = self.articleUrl
        url += articleId
        headers = dict()
        payload = dict()
        headers['User-Agent'] = 'NewsApp/29.1 iOS/11.0.3 (iPhone8,1)'
        try:
            r = requests.get(url, headers=headers, params=payload, timeout = 3)
            r = r.json()
            r = r['body']
        except:
            traceback.print_exc()
            return None
        else:
            if 'title' not in r.keys():
                return None
            title = r['title']
            if title == None:
                return None
            webUrl = r['shareurl']
            webUrl = utils.formatUrl(webUrl)
            if utils.checkVisited(webUrl, db):
                return -1
            content = r['text']
            content = utils.formatContent(content)
            appUrl = url
            publishTime = r['updateTime']
            news = utils.News(title, appUrl, webUrl, content, publishTime, source)
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
                r = requests.get(url, params=payload, headers=headers, timeout = 3)
                r = r.json()
                commentList = r['data']
            except requests.exceptions.ConnectTimeout:
                traceback.print_exc()
                break
            except:
                payload['page'] = payload['page'] + 1
                traceback.print_exc()
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
                        userName = utils.formatContent(comment['nickname'])
                        userName = utils.formatComment(userName)
                    else:
                        userName = '匿名用户'
                    content = utils.formatContent(comment['data']['comment_contents'])
                    content = utils.formatComment(content)
                    content1 = publishTime + ' ' + userName + ' ' + content
                    commentList1.append(content1)
                offset += count
        return commentList1
    
def main():
    cateUrl = 'https://api.iclient.ifeng.com/ClientNews'
    articleUrl = ''
    commentUrl = 'https://user.iclient.ifeng.com/Social_Api_Comment/getCommentList'
    db = utils.Mysql('localhost', 'root', 'informationRetrieval', 'information_retrieval')
    source = 'ifengNewsApp'
    ifengAppCrawler = Crawler(cateUrl, articleUrl, commentUrl)
    cateIdDict = readConf();
    ifengAppCrawler.cateIdDict = cateIdDict
    cateNewsDict = ifengAppCrawler.getCateNews()
    for cate, newsList in cateNewsDict.items():
        print('category: ' + cate)
        print('count of article:' + str(len(newsList)))
        number = 1
        duplicateCount = 0
        failCount = 0
        for news in newsList:
            articleId = news['articleId']
            commentUrl = news['commentUrl']
            commentNum = news['commentNum']
            if number % 50 == 0:
                print("handle  " + str(number) + '    duplicateCount: ' + str(duplicateCount) + '   failCount:  '  + str(failCount))
            number += 1
            news = ifengAppCrawler.getArticle(db, articleId, source)
            if news == None:
                failCount += 1
                continue
            if news == -1:
                duplicateCount += 1
                continue
            if commentNum != '':
                news.commentCount = commentNum
            commentList = ifengAppCrawler.getComment(commentUrl, min(100, int(news.commentCount)))
            news.category = cate
            news.commentList = commentList
            utils.storeToDb(news, db)
    db.connection.close()

def readConf():
    cateIdDict = dict()

    cateIdDict['society'] = ('NXWPD,FOCUSNXWPD', 2000)
    cateIdDict['technology'] = ('KJ123,FOCUSKJ123', 2000)
    cateIdDict['finance'] = ('CJ33,FOCUSCJ33,HNCJ33', 2000)
    cateIdDict['sport'] = ('TY43,FOCUSTY43,TYLIVE', 2000)
    cateIdDict['military'] = ('JS83,FOCUSJS83', 2000)
    cateIdDict['entertainment'] = ('YL53,FOCUSYL53', 2000)
    cateIdDict['nba'] = ('NXWPD,FOCUSNXWPD', 2000)
    cateIdDict['politics'] = ('SZPD,FOCUSSZPD', 2000)
    return cateIdDict
if __name__ == '__main__':
    main()
