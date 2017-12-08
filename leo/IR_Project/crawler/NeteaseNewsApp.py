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
            maxTime = 200
            currentTime = 0
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
                if currentTime > maxTime:
                    break
                currentTime += 1
                if kind == 0:
                    url = self.cateUrl1 + value[1] + '/' + str(offset) + '-20.html'
                    offset = offset + 20
                if kind == 1:
                    payload['offset'] = offset
                    offset = offset + 0
                #print(url)
                try:
                    r = requests.get(url, params=payload,  headers=headers, timeout = 3)
                    r = r.json()
                except requests.exceptions.ConnectTimeout:
                    traceback.print_exc()
                    break
                except:
                    traceback.print_exc()
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
                        break
            cateArticleIdDict[cate] = articleIdSet
        return cateArticleIdDict
    
    def getSpecialArticleId(self, specialId):
        url = self.specialNewsUrl + specialId + '.html'
        headers = dict()
        headers['User-Agent'] = 'NewsApp/29.1 iOS/11.0.3 (iPhone8,1)'
        r = requests.get(url, headers=headers)
        docIdSet = set()
        try:
            r = requests.get(url, headers=headers, timeout = 3)
            r = r.json()
            topicList = r[specialId]['topics']
        except:
            traceback.print_exc()
        else:
            for topic in topicList:
                docList = topic['docs']
                for doc in docList:
                    docId = doc['docid']
                    docIdSet.add(docId)
        return docIdSet
        
    def getArticle( self, db, articleId, source):
        #print('getArticle')
        url = self.articleUrl + articleId  + '/full.html'
        #print(url)
        headers = dict()
        headers['User-Agent'] = 'NewsApp/29.1 iOS/11.0.3 (iPhone8,1)'
        try:
            r = requests.get(url, headers=headers, timeout = 3)
            r = r.json()
        except:
            traceback.print_exc()
            return None
        else:
            r = r[articleId]
            if 'title' not in r.keys():
                return None
            title = r['title']
            if title == None:
                return None
            webUrl = r['shareLink']
            webUrl = utils.formatUrl(webUrl)
            if utils.checkVisited(webUrl, db):
                return -1
            content = r['body']
            content = utils.formatContent(content)
            appUrl = url
            commentCount = r['replyCount']
            upCount = r['threadVote']
            downCount = r['threadAgainst']
            publishTime = r['ptime']
            news = utils.News(title, appUrl, webUrl, content, publishTime, source)
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
                r = requests.get(url, params=payload, headers=headers, timeout = 3)
                r = r.json()
            #except requests.exceptions.ConnectTimeout:
                #traceback.print_exc()
                #break
            except requests.exceptions.Timeout:
                offset += (Limit + payload['headLimit'] + payload['tailLimit'])
                traceback.print_exc()
            except:
                traceback.print_exc()
                break
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
                        userName = utils.formatContent(comment['user']['nickname'])
                        userName = utils.formatComment(userName)
                    else:
                        userName = '匿名用户'
                    content = utils.formatContent(comment['content'])
                    content = utils.formatComment(content)
                    content1 = publishTime + ' ' + userName + ' ' + content
                    commentList.append(content1)
                offset += count
        return commentList
    

def main():
    articleUrl = 'https://c.m.163.com/nc/article/'
    commentUrl = 'https://comment.api.163.com/api/v1/products/a2869674571f77b5a0867c3d71db5856/threads/'
    cateUrl1 = 'https://c.m.163.com/nc/article/list/'
    cateUrl2 = 'https://c.m.163.com/dlist/article/dynamic'
    specialNewsUrl = 'https://c.m.163.com/nc/special/'
    db = utils.Mysql('localhost', 'root', 'informationRetrieval', 'information_retrieval')
    source = 'NeteaseNewsApp'
    neteaseAppCrawler = Crawler(cateUrl1, cateUrl2, articleUrl, commentUrl)
    neteaseAppCrawler.specialNewsUrl = specialNewsUrl
    cateIdDict = readConf();
    neteaseAppCrawler.cateIdDict = cateIdDict
    cateArticleIdDict = neteaseAppCrawler.getCateArticleId()
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
            news = neteaseAppCrawler.getArticle(db, articleId, source)
            if news == None:
                failCount += 1
                continue
            if news == -1:
                duplicateCount += 1
                continue
            #网易的锅，无法显示全部评论
            commentList = neteaseAppCrawler.getComment(articleId, min(news.commentCount, 100))
            news.category = cate
            news.commentList = commentList
            utils.storeToDb(news, db)

    db.connection.close()

def readConf():
    cateIdDict = dict()
    cateIdDict['politics'] = (0, 'T1414142214384', 1000)
    cateIdDict['society'] = (1, 'T1348648037603', 1500)
    cateIdDict['technology'] = (1, 'T1348649580692', 1500)
    cateIdDict['finance'] = (1, 'T1348648756099', 1500)
    cateIdDict['sport'] = (1, 'T1348649079062', 1500)
    cateIdDict['military'] = (1, 'T1348648141035', 1500)
    cateIdDict['entertainment'] = (1, 'T1348648517839', 1500)
    cateIdDict['NBA'] = (1, 'T1348649145984', 1500)
    return cateIdDict
if __name__ == '__main__':
    main()
