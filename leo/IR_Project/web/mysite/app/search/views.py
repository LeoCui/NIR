from django.shortcuts import render
# Create your views here.
from django.http import HttpResponse
import json
from django.utils.safestring import SafeString
from django.shortcuts import get_object_or_404, render
def index(request):
    return render(request, 'search/index.html')
def result(request):
    result = dict()
    newsList = list()
    news = dict()
    keywords = list()
    keywords.append('情敌')
    keywords.append('大学生')
    news['title'] = '女大学生实习时移情有妇之夫 男友为泄愤刺死情敌';
    news['content'] = '俗话说冲动是魔鬼，男女恋爱本来是甜蜜的，然而在读大一的大学生王某因为女友邵某移情别恋提出分手，他竟然将情敌李某一刀刺死，近日，王某因涉嫌故意伤害罪被浦东新区人民检察院批准逮捕。经查，今年7月30号晚上7点30分，来沪实习的河南郑州成功财经学院大一学生王某接到女友邵某电话，称其已和别人发生关系，要求和王某分手。王某接完电话后，就带着一把水果刀，通过邵某找到与其发生关系的李某。犯罪嫌疑人王某：“李某走的时候他突然转身骂我，还准备打我，在这时候我脑子已经一片空白，就已经啥也不知道了，拿着刀怎么就捅他了。等我清醒的时候刀已经在他身上了。”经鉴定，被害人李某系生前被他人用锐器刺戳背部，导致肝脏、肾脏破裂而失血性休克死亡。审讯中，王某对自己的犯罪行为供认不讳，据王某交代，他与女友邵某';
    news['keywords'] = keywords
    news['source'] = '网易新闻'
    news['commentCount'] = 20
    news['url'] = 'https://c.m.163.com/news/a/D5MI07OT0001899N.html?spss=newsapp'
    news['category'] = '社会'
    news['publishTime'] = '2017-12-18'
    news['relationship'] = '91.27%' 
    newsList.append(news)
    result['newsList'] = newsList
    result['page'] = 1
    result['resultCount'] = 2 
    result['cost'] = 0.21
    # 4个
    relatedNewsList = list()
    relatedNewsList.append('女大学生')
    relatedNewsList.append('情妇')
    relatedNewsList.append('有妇之夫')
    relatedNewsList.append('有妇之夫')
    searchHistory = list()
    searchHistory.append('大学生')
    searchHistory.append('大火')
    searchHistory.append('川普')
    searchHistory.append('习大大')
    result['relatedNewsList'] = relatedNewsList 
    result['searchHistory'] = searchHistory
    return render(request, 'search/result.html', {'result': result})



