# -*- coding: utf-8 -*-
from datetime import datetime

from django.shortcuts import render
from blueking.component.shortcuts import get_client_by_user
import logging, copy, base64
from django.http.response import JsonResponse
from django.template.loader import render_to_string
from .celery_tasks import async_status
from .models import Doinfo

client = get_client_by_user("awjliu")
logger = logging.getLogger(__name__)


# 查询业务
def get_biz_info():
    kwargs = {"fields": ["bk_biz_id", "bk_biz_name"]}
    res = client.cc.search_business(kwargs)
    biz_name = []
    biz_id = []
    biz = {}
    if res.get('result', False):
        for i in res['data']['info']:
            biz_name.append(i['bk_biz_name'])
            biz_id.append(i['bk_biz_id'])
            biz = dict(zip(biz_name, biz_id))
    else:
        logger.error(u'请求业务列表失败：%s' % res.get('message'))
    return biz


# 根据业务ID查询集群
def get_set_info(id):
    kwargs = {"bk_biz_id": id}
    res = client.cc.search_set(kwargs)
    set = []
    if res.get('result', False):
        for set_info in res['data']['info']:
            set.append({
                "set_id": set_info['bk_set_id'],
                "set_name": set_info['bk_set_name'],
            })
    else:
        logger.error(u'请求业务集群列表失败：%s' % res.get('message'))
    return set


# 根据业务ID,集群ID查询主机
def ser_host(biz_id, set_id):
    kwargs = {"bk_biz_id": biz_id,
              "condition": [{"bk_obj_id": "set",
                             "fields": [],
                             "condition": [{"field": "bk_set_id",
                                            "operator": "$eq",
                                            "value": int(set_id)}]
                           }]}
    res = client.cc.search_host(kwargs)
    hosts = []
    if res.get('result', False):
        if res['data']['info'] != 0:
            for host_info in res['data']['info']:
                hosts.append({
                    "count": res['data']['count'],
                    "ip": host_info['host']['bk_host_innerip'],
                    "os": host_info['host']["bk_os_name"],
                    "host_id": host_info['host']["bk_host_id"],
                    "name": host_info['host']['bk_host_name'],
                    "cloud_id": host_info['host']["bk_cloud_id"][0]["id"]
                })
        else:
            return hosts
    else:
        logger.error(u'查询主机列表失败：%s' % res.get('message'))
    return hosts


# 刷新集群信息
def get_set(request):
    biz_id = request.GET.get('biz_id')
    if biz_id:
        biz_id = int(biz_id)
    else:
        return JsonResponse({'result': False, 'message': "must provide biz_id to get set"})
    data = get_set_info(biz_id)
    select_data = render_to_string('home_application/home_tbody.html', {'data': data})
    return JsonResponse({"result": True, "message": "success", "data": select_data})


# 刷新主机信息
def get_host(request):
    biz_id = request.GET.get('biz_id')
    set_id = request.GET.get('set_id')
    if biz_id:
        biz_id = int(biz_id)
    else:
        return JsonResponse({'result': False, 'message': "must provide biz_id to get hosts"})
    data = ser_host(biz_id, set_id)
    table_data = render_to_string('home_application/host_tbody.html', {'data': data})
    return JsonResponse({"result": True, "message": "success", "data": table_data})


# 执行任务
def execute_script(request):
    biz_id = request.POST.get('biz_id')
    set_id = request.POST.get('set_id')
    user = request.user

    data = ser_host(biz_id, set_id)
    script = '''#!/bin/bash
                MEMORY=$(free -m | awk 'NR==2{printf "%.2f%%", $3*100/$2 }')
                DISK=$(df -h | awk '$NF=="/"{printf "%s", $5}')
                CPU=$(top -bn1 | grep load | awk '{printf "%.2f%%", $(NF-2)}')
                echo -e "$MEMORY|$DISK|$CPU"
             '''
    encodestr = base64.b64encode(script.encode('utf-8'))
    script_content = str(encodestr, 'utf-8')
    if data:
        ip_id = []
        ip_info = []
        ips = {"bk_cloud_id": 0, "ip": 0}
        for info in data:
            ip_id.append(info['ip'])
            ips['ip'] = info['ip']
            ip_info.append(copy.deepcopy(ips))
        kwargs = {"bk_biz_id": int(biz_id),
                  "script_content": script_content,
                  "account": "root",
                  "script_type": 1,
                  "ip_list": ip_info}
        execute_data = client.job.fast_execute_script(kwargs)
        if execute_data.get('result', False):
            data = execute_data['data']
            result = True
            message = str(execute_data.get('message'))
            async_status.apply_async(args=[client, data, biz_id, ip_id, user], kwargs={})
        else:
            data = []
            result = False
            message = "False"
            logger.error(u'查询主机列表失败：%s' % execute_data.get('message'))
        return JsonResponse({"result": result, "message": message, "data": data})
    else:
        return JsonResponse({'result': False, 'message': "There must be a host under the cluster", 'data': []})


def home(request):
    data = {"biz": get_biz_info().items(),
            "set": get_set_info(2)
            }
    return render(request, 'home_application/home.html', data)


def record(request):
    doinfos = Doinfo.objects.all()
    data = {"biz": get_biz_info().items(),
            "doinfos": doinfos}
    return render(request, 'home_application/record.html', data)


# 根据前端返回的数据进行查询
def inquiry(request):
    try:
        biz_id = request.POST.get('biz_id')
        kwargs3 = {"fields": ["bk_biz_id", "bk_biz_name"], "condition": {"bk_biz_id": int(biz_id)}}
        res2 = client.cc.search_business(kwargs3)
        biz_name = res2['data']['info'][0]['bk_biz_name']
        time = request.POST.get('time')  #"2020-04-22 00:00:00 ~ 2020-04-22 23:59:59"
        doinfo = Doinfo.objects.all()
        doinfo = doinfo.filter(businessname=biz_name)
        starttime, endtime = time.split('~')
        doinfo = doinfo.filter(starttime__range=(starttime.strip(), endtime.strip()))
        data = [info.to_dict() for info in doinfo]
        # print(data)
        table_data = render_to_string('home_application/record_tbody.html', {'doinfos': data})
        result = True
        message = "success"
    except Exception as err:
        table_data = []
        result = False
        message = str(err)
    return JsonResponse({"result": result, "message": message, "data": table_data})

