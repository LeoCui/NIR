from  lib.utils import *
import sys
import time
import datetime
import math

class NewsInfo:
    def __init__(self, newsId, pv, commentNumber, publishTime):
        self.newsId = newsId
        self.pv = pv
        self.commentNumber = commentNumber
        self.publishTime = publishTime
        self.score = 0

def sortNews(db, newsList, currentTime):
    currentTime = time.mktime(currentTime)
    for news in newsList:
        score = 0
        pv = news.pv
        commentNumber = news.commentNumber
        pv = pv / 100000.0
        commentNumber = commentNumber / 100000.0
        if pv == -1:
            pv = 0
        if commentNumber == -1:
            commentNumber = 0
        publishTime = news.publishTime
        publishTime = time.strptime(publishTime, "%Y-%m-%d %H:%M:%S")
        publishTime = time.mktime(publishTime)
        interval = publishTime - currentTime
        interval = interval / 100000.0
        interval = float(interval)
        score1 = 1.0 / (math.exp(0 - pv) + 1)
        score2 = 1.0 / (math.exp(0 - commentNumber) + 1)
        score3 = math.exp(interval) 
        score = score1 * score2 * score3
        news.score = score
    newsList = sorted(newsList, key=lambda x:x.score, reverse=True)
    for i in range(0,10):
        news = newsList[i]
        valueDict = dict()
        print(news.score)
        valueDict['news_id'] = news.newsId
        db.insert('hot_news', valueDict)
        db.connection.commit()

def main():
    newsList = list()
    currentTime = time.localtime()
    queryStartTime = time.mktime(currentTime) - 86400*3
    queryStartTime = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(queryStartTime))
    db = Mysql('localhost', 'root', 'informationRetrieval', 'information_retrieval')
    queryList = ('id', 'pv', 'comment_number', 'publish_time', 'url')
    conds = "where publish_time>'" + queryStartTime + "'"
    results = db.select('news_info', queryList, conds)
    for result in results:
        newsId = result[0]
        pv = result[1]
        commentNumber = result[2]
        publishTime = str(result[3])
        url = result[4]
        if 'weixin' in url:
            continue
        newsInfo = NewsInfo(newsId, pv, commentNumber, publishTime)
        newsList.append(newsInfo)
    sortNews(db, newsList, currentTime)
    db.connection.close()
if __name__ == '__main__':
    main()



