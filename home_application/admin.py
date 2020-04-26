# -*- coding: utf-8 -*-
from django.contrib import admin
from .models import Doinfo
# Register your models here.


class Info(admin.ModelAdmin):
    list_display = ['businessname', 'username', 'jobid', 'starttime', 'iplist', 'status', 'log']
    search_fields = ['businessname', 'username', 'jobid']
    date_hierarchy = 'starttime'
    list_filter = ['businessname', 'username']


admin.site.register(Doinfo, Info)