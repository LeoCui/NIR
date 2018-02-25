import json
import jieba
import re
import math
import time
import traceback
from zlib import crc32
import numpy

class DocRank(object):

    def __init__(self, posting_list, db, stop_word, docsSize, lengthDict, avgLength):

        #倒排记录表
        self.posting_list = posting_list
        #数据库操作
        self.db = db
        #停用词表
        self.stop_word = stop_word
        #文档总数量
        self.docsSize = docsSize
        #每页显示文档数
        self.pageNumber = 10
        #文档长度
        self.lengthDict = lengthDict
        #文档平均长度
        self.avgLength = avgLength

    #文档排序
    def query(self, json_input):
        print(json_input)
    	#读取json
        data_input = json_input

        query = data_input['query'].lower()
        source = data_input['source']
        category = data_input['category']
        time_from = data_input['from']
        time_to = data_input['to']
        sortType = int(data_input['sort'])
        page = int(data_input['page'])

        if '*' in query:
            #通配符查询相关文档
            ans = self.queryByWildcard(query, source, category, time_from, time_to, sortType, page, 5)
        else:
            #词项查询相关文档
            ans = self.queryByTerms(0, query, source, category, time_from, time_to, sortType, page)
        return ans


    #词项查询相关文档
    def queryByTerms(self, W, query, source, category, time_from, time_to, sortType, page):

        #分词
        if W == 0:
            terms = self.wordSegment(query)
        else:
            terms = [x for x in query]

        #删除停用词
        for term in terms:
            if term in self.stop_word:
                terms.remove(term)
        print("-----term:", len(terms))
        
        #倒排记录表求交
        intersection = self.intersectPostingList(terms)
        print("-----intersect result:", len(intersection))

        #Wt_q
        Wt_q = self.calculateWt_q(terms)
        print("-----calculateWt_q:", len(Wt_q))
        
        #过滤文档
        if source != 'all' or category != 'all' or time_from != 'all' or time_to != 'all':
            intersection = self.filterDocsByTSC(intersection, source, category, time_from, time_to)
            print("filterd")
        
        #文档排序
        if sortType == 0:
            scores, rank = self.rankDocsByTfidf(Wt_q, intersection)
        else:
            scores, rank = self.rankDocsByTime(Wt_q, intersection)
        print("-----rankDocs:", len(scores), len(rank))

    	#相关文档总数
        relatedDocSize = len(intersection)

    	#选区指定页数文档
        if page >= 0:
            result = self.filterPage(rank, page)
        else:
            result = rank
        print("-----filterPage", len(result))

    	#构造输出
        docList = list()
        for docID in result:
            docList.append({'id':docID, 'relationship':scores[docID]})

        output = dict()
        output['resultCount'] = relatedDocSize
        output['keywords'] = terms
        output['docList'] = docList


        return output


    #通配符查询
    def queryByWildcard(self, query, source, category, time_from, time_to, sortType, page, limit):
        #k-gram分词
        query = "$"+query+"$"
        grams = self.wordSegmentByKgram(query, 2)
        print("grams", grams)
        terms = self.getTermsByKgram(grams, limit)
        print("wildcard---terms", len(terms))
        print(terms)
        
        #相关文档数
        relatedDocCount = 0

        #查询terms相关文档
        docs = list()       #保存最终List
        alldocs = list()    #保存查询List
        for term in terms:
            result = self.queryByTerms(1, term, source, category, time_from, time_to, sortType, -1)
            alldocs.extend(result['docList'])
            #relatedDocCount = max(int(result['resultCount'])/10, relatedDocCount)
        alldocs = sorted(alldocs, key=lambda x: float(x['relationship']), reverse=True)
        relatedDocCount = len(alldocs)
        print("wildcard---alldocs:", len(alldocs))

       # for i in range(self.pageNumber):
       #     for term in terms:
       #         if i < len(alldocs[term]):
       #             docs.append(alldocs[term][i])
       #         if len(docs) >= self.pageNumber:
       #             break
        docs = self.filterPage(alldocs, page)
        print("wildcard---docs:", len(docs))
        #docs = sorted(docs, key=lambda x: float(x['relationship']), reverse=True)
        output = dict()
        output['resultCount'] = relatedDocCount
        output['keywords'] = terms
        output['docList'] = docs
        print("wildcard---output:", output)
    
        return output

    #分词
    def wordSegment(self, query):

        pattern = re.compile(r"(\s)*")
        query, number = pattern.subn("", query)

        terms = jieba.cut(query)
        return [x for x in terms]


    #倒排记录表求交
    def intersectPostingList(self, terms):

        inter = set()
        flag = 0

        for term in terms:
            if term in self.posting_list.keys():
                posting_list = self.posting_list[term]['docDict']
                tmp = set(posting_list.keys())
                if flag == 0:
                    inter.update(posting_list.keys())
                    flag = 1
                else:
                    if len(tmp) != 0:
                        inter = inter & tmp
        return list(inter)

    #计算Wt_q
    def calculateWt_q(self, terms):

    	#查询tf值
    	tfs = dict()
    	#Wt_q
    	Wt_q = dict()

    	#长度，用于归一化
    	length = 0

    	for term in terms:
            if term in tfs.keys():
                tfs[term] += 1
            else:
                tfs[term] = 1

    	for term in tfs.keys():
            if term in self.posting_list.keys():
                df = self.posting_list[term]['df'] * 1.0
            else:
                df = 0
            idf = 0.

            idf = math.log((self.docsSize-df+0.5)/(df+0.5), 10)

            Wt_q[term] = idf

            length += Wt_q[term] ** 2

    	length = math.sqrt(length)

    	#归一化
    	#if length != 0:
        #    for term in Wt_q.keys():
        #        Wt_q[term] = Wt_q[term] / length

    	return Wt_q

    #文档按tf-idf排序
    def rankDocsByTfidf(self, Wt_q, intersection):

    	docScores = dict()

    	for docID in intersection:
            docScores[docID] = self.calculateSimilarity(Wt_q, docID)

    	rank = sorted(docScores.items(), key=lambda x: x[1], reverse=True)
    	rank = [x[0] for x in rank]

    	return docScores, rank

    #文档按时间排序
    def rankDocsByTime(self, Wt_q, intersection):
        docsTime = dict()
        try:
            for docID in intersection:
                queryList = list()
                queryList.append('publish_time')
                t = self.db.select('news_info', queryList, "where id = " + docID)
        
                docsTime[docID] = self.timeStr2Integer(str(t[0][0]))
        except Exception as e:
            print(e)

        rank = sorted(docsTime.items(), key=lambda x: x[1], reverse=True)
        rank = [x[0] for x in rank]
        docScores = dict()
        for docID in intersection:
            docScores[docID] = self.calculateSimilarity(Wt_q, docID)

        return docScores, rank

    #相关度计算
    def calculateSimilarity(self, Wt_q, docID):
        Wt_d = dict()
        length = 0
        score = 0

        '''
        for term in Wt_q.keys():
            if term in self.posting_list.keys():
                tf = int(self.posting_list[term]['docDict'][docID])
            else:
                tf = 0
            idf = 1.
            Wt_d[term] = self.calculateWF(tf) * idf
            length += Wt_d[term] ** 2

        length = math.sqrt(length)

        #归一化
        if length != 0:
            for term in Wt_d.keys():
                Wt_d[term] = Wt_d[term] / length

        #计算余弦相似度
        for term in Wt_q.keys():
            score += Wt_q[term] * Wt_d[term]
        '''
        for term in Wt_q.keys():
            if term in self.posting_list.keys():
                tf = int(self.posting_list[term]['docDict'][docID])
            else:
                tf = 0
            docLength = 0.
            if docID in self.lengthDict.keys():
                docLength = self.lengthDict[docID]
            score += Wt_q[term] * ((2.5*tf)/(1.5*(0.25+0.75*(docLength/self.avgLength)) + tf))
            
        score = numpy.tanh(score/5.0)
        return score

    #文档筛选
    def filterDocsByTSC(self, relatedDocs, source, category, time_from, time_to):
        filtered = list()
        if time_from != 'all':
            t_from = self.timeStr2Integer(time_from)
        if time_to != 'all':
            t_to = self.timeStr2Integer(time_to)
        try:
            for docID in relatedDocs:
                flag = True
                queryList = list()
                queryList.append('source')
                queryList.append('category')
                queryList.append('publish_time')

                result = self.db.select('news_info', queryList, "where id = " + docID)
    
                if result[0][0] is None or result[0][1] is None or result[0][2] is None:
                    continue

                if source != 'all' and source != result[0][0]:
                    flag = False
                if category != 'all' and category != result[0][1]:
                    flag = False
                if time_from != 'all' and time_to != 'all':
                    t = self.timeStr2Integer(str(result[0][2]))
                    if(not (t_from <= t <= t_to)):
                        flag = False
                elif time_from != 'all' and time_to == 'all':
                    t = self.timeStr2Integer(str(result[0][2]))
                    if t < t_from:
                        flag = False
                elif time_from == 'all' and time_to != 'all':
                    t = self.timeStr2Integer(str(result[0][2]))
                    if t > t_to:
                        flag = False

                if flag:
                    filtered.append(docID)
        except Exception as e:
            print(e)

        return filtered
        
    #k-gram分词
    def wordSegmentByKgram(self, query, k):
        ans = list()
        segments = query.split("*")
        for seg in segments:
            tmp = list()
            for i in range(len(seg)-k+1):
                tmp.append(seg[i:i+k])
            ans.extend(tmp)
        return ans

    #根据k-gram查询可能的词项
    def getTermsByKgram(self, grams, limit):
        intersection = set()
        flag = 0
        try:
            for gram in grams:
                ids = self.getTermsFromKgram(gram)
                tmp = set(ids)
                if flag == 0:
                    intersection = intersection | tmp
                    flag = 1
                else:
                    intersection = intersection & tmp

            intersection = list(intersection)
            if limit < len(intersection):
                intersection = intersection[0:limit]

            ans = list()
            for termID in intersection:
                queryList = list()
                queryList.append('term')
                result = self.db.select('dictionary', queryList, "where id = " + termID)
                ans.append(result[0][0])


        except Exception as e:
            print(e)

        return ans

    #查询kgram表
    def getTermsFromKgram(self, gram):
        ans = set()

        queryList = list()
        queryList.append('kgram')
        queryList.append('content')
        hash_value = crc32(bytes(gram, 'utf8'))
        result = self.db.select('kgram_index', queryList, "where kgram_hash = " + str(hash_value))
        for record in result:
            if record[0] == gram:
                content = record[1]
                ids = content[1:-1].split(',')
                ans.update(ids)

        return list(ans)

    #选取指定page的文档
    def filterPage(self, rank, page):
        filterd = list()
        for i in range((page-1)*self.pageNumber, page*self.pageNumber):
            if i < len(rank):
                filterd.append(rank[i])

        return filterd

    #时间字符串转整形
    def timeStr2Integer(self, timeStr):
        times = time.strptime(timeStr, '%Y-%m-%d %H:%M:%S')
        return time.mktime(times)

    #tf的亚线性尺度变换
    def calculateWF(self, tf):
        if int(tf) > 0:
            return 1 + math.log(tf, 10)
        else:
            return 0

