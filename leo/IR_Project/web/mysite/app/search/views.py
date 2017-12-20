import sys
sys.path.append("/Users/Leo/Documents/github/NIR/leo/IR_Project/web/mysite/app/search/")
#print(sys.path)
from django.shortcuts import render
# Create your views here.
from django.http import HttpResponse
import json
from django.utils.safestring import SafeString
from django.shortcuts import get_object_or_404, render
import time
import lib.utils as utils
import math
import requests
import traceback
import subprocess

def index(request):
    return render(request, 'search/index.html')

def getInput(request):
    query = request.GET.get('query')
    page = request.GET.get('page')
    category = request.GET.get('category')
    source = request.GET.get('source')
    date = request.GET.get('date')
    sort = request.GET.get('sort')
    input = dict()
    input['query'] = ''
    input['page'] = 1
    input['category'] = 'all'
    input['source'] = 'all'
    input['from'] = 'all'
    input['to'] = 'all'
    input['sort'] = 0
    if query != None:
        input['query'] = query
    if page != None:
        input['page'] = page
    if category != None:
        input['category'] = category
    if source != None:
        input['source'] = source
    if sort != None:
        input['sort'] = sort
    if date != None:
        endTime = time.time() + 3600*8
        if date == "today":
            beginTime = endTime - 86400
        if date == 'threeDays':
            beginTime = endTime - 86400*3
        if date == 'thisWeek':
            beginTime = endTime - 86400*7
        input['from'] = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(beginTime))
        input['to'] = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(endTime))
    return input

def getOutput(input, db, startTime):
    output = dict()
    #调用jar包
    queryResult = invokeJar(input)
    output['resultCount'] = 0
    output['keywords'] = list()
    output['query'] = input['query']
    output['newsList'] = list()
    print(queryResult)
    if queryResult != None and 'resultCount' in queryResult.keys():
        output['resultCount'] = queryResult['resultCount']
    if queryResult != None and 'keywords' in queryResult.keys():
        output['keywords'] = queryResult['keywords'] 
    if queryResult != None and 'docList' in queryResult.keys():
        output['newsList'] = getNewsList(queryResult, db)
    output['page'] = input['page']
    output['relatedNewsList'] = getRelatedSearch(input['query'], 4)
    output['searchHistory'] = getSearchHistory(db, 4)
    output['category'] = getCurrentCate(input['category']) 
    endTime = time.time()
    cost = endTime - startTime
    cost = round(cost,2)
    output['cost'] = cost
    return output

def invokeJar(input):

    input = json.dumps(input)
    input = input.replace("\"","\\\"")
    input = "\"" + input + "\""
    command = "cd /Users/Leo/Documents/github/NIR/leo/IR_Project/web/mysite/app/search/lib/doc_rank && "
    command = command + "java -jar docrank-1.0.4.jar " + input
    #print('command: '+ command)
    queryResult = None
    try:
        out_bytes = subprocess.check_output(command,shell=True)
        out_str = out_bytes.decode()
        queryResult = json.loads(out_str)
    except:
        traceback.print_exc()
    return queryResult 

def getRelatedSearch(query,num):
    result = list()
    payload = dict()
    payload['query'] = query
    url = 'http://api.bing.com/osjson.aspx'
    try:
       r = requests.get(url, params=payload, timeout=0.5)
       r = r.json()
    except:
       traceback.print_exc()
       return  result
    result = r[1][0:num]
    print(result)
    return result 
    
def getSearchHistory(db,num):
    queryList = list()
    queryList.append('content')
    conds = 'order by id desc limit ' + str(num)
    tableName = 'search_history'
    results = db.select(tableName, queryList, conds)
    results1 = list()
    for result in results:
        results1.append(result[0])
    return results1

def getCurrentCate(category):
    currentCateDict = dict()
    if category != None:
        currentCateDict[category] = 'current'
    return currentCateDict

def getNewsList(queryResult, db):
    cateDict = dict()
    cateDict['politics'] = '政务'
    cateDict['sport'] = '体育'
    cateDict['NBA'] = '体育'
    cateDict['international'] = '国际'
    cateDict['military'] = '军事'
    cateDict['society'] = '社会'
    cateDict['beijing'] = '社会'
    cateDict['technology'] = '科技'
    cateDict['entertainment'] = '娱乐'
    cateDict['hotNews'] = '社会'
    cateDict['taiwan'] = '军事'
    cateDict['finance'] = '财经'
    sourceDict = dict()
    sourceDict['cctvNewsApp'] = '央视新闻'
    sourceDict['IfengNewsApp'] = '凤凰新闻'
    sourceDict['NeteaseNewsApp'] = '网易新闻'
    sourceDict['SohuNewsApp'] = '搜狐新闻'
    newsList = list()
    docList = queryResult['docList']
    keywords = queryResult['keywords']
    for doc in docList:
        news_id = doc['id']
        relationship = float(doc['relationship'])
        relationship = relationship * 100
        relationship = round(relationship,2)
        relationship = str(relationship) + '%'
        #news_info
        tableName = 'news_info'
        queryList = list()
        queryList.append('title')
        queryList.append('source')
        queryList.append('pv')
        queryList.append('url')
        queryList.append('category')
        queryList.append('publish_time')
        conds = 'where id=' + str(news_id)
        results = db.select(tableName, queryList, conds)
        if results == None or len(results)==0:
            continue
        result = results[0]
        news = dict()
        news['title'] = result[0]
        news['source'] = sourceDict[result[1]]
        news['pv'] = result[2]
        if int(news['pv']) == -1:
            news['pv'] = '未知'
        news['url'] = result[3]
        publishTime = str(result[5])
        publishTimeList = publishTime.split()
        publishDate = publishTimeList[0]
        news['publishTime'] = publishDate
        news['category'] = cateDict[result[4]]
        news['relationship'] = relationship
        #content_info
        content = ''
        tableName = 'content_info'
        queryList = list()
        queryList.append('content')
        conds = 'where news_id=' + str(news_id) + ' order by sequence_number'
        results = db.select(tableName, queryList, conds)
        if results == None or len(results)==0:
            continue
        for result in results:
            content = content + result[0]
        #comment_info 
        tableName = 'comment_info'
        queryList = list()
        queryList.append('content')
        conds = 'where news_id= ' + str(news_id)
        results = db.select(tableName, queryList, conds)
        for result in results:
            temp = result[0]
            temp = temp.replace('|',' ')
            content = content + temp
        content = getAbstract(content, keywords, 100)
        news['content'] = content
        newsList.append(news)
    return newsList

def getAbstract(content, keywords, maxNum):
    len1 = len(content)
    maxCount = -1
    result = ''
    for i in range(0, len1-maxNum+1):
        count = 0
        str1 = content[i:i+maxNum+1]
        for keyword in keywords:
            if keyword in str1:
                count += 1
        if count > maxCount:
            maxCount = count
            result = str1
    return result


def recordSearchHistory(input,db):
    if input == None or input['query']=='':
        return
    query = input['query']
    valueDict =dict()
    valueDict['content'] = query
    tableName = 'search_history'
    db.insert(tableName, valueDict) 
    db.connection.commit()
    return 

def result(request):
    startTime = time.time()
    db = utils.Mysql('localhost','root','informationRetrieval','information_retrieval')
    input = getInput(request)
    #print(input)
    recordSearchHistory(input,db)
    output = getOutput(input, db,startTime)
    db.connection.close()
    return render(request, 'search/result.html', {'result': output})

