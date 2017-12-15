from django.shortcuts import render
# Create your views here.
from django.http import HttpResponse
import json
from django.utils.safestring import SafeString
from django.shortcuts import get_object_or_404, render
def index(request):
    return render(request, 'search/index.html')
def result(request):
    resultList = list()
    result = dict()
    result['title'] = '雷军：小米新旗舰明年年初发布 搭载骁龙845'
    result['keyword'] = '雷军'
    resultList.append(result)
    resultList.append(result)
    resultList.append(result)
    resultList.append(result)
    print(result)
    return render(request, 'search/result.html', {'resultList': resultList})



