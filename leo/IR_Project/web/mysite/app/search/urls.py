#! /usr/bin/env python
#################################################################################
#     File Name           :     urls.py
#     Created By          :     Leo
#     Creation Date       :     [2017-11-30 17:55]
#     Last Modified       :     [2017-12-06 14:41]
#     Description         :      
#################################################################################
from django.conf.urls import url
from . import views
urlpatterns = [
        url(r'^$', views.index),
        url(r'^result.html$', views.result),
]
