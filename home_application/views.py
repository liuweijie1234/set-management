# -*- coding: utf-8 -*-
from django.shortcuts import render
from blueking.component.shortcuts import get_client_by_user
import logging
from django.http.response import JsonResponse
from django.template.loader import render_to_string


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
              "condition": [
                  {
                      "bk_obj_id": "set",
                      "fields": [],
                      "condition": [{
                          "field": "bk_set_id",
                          "operator": "$eq",
                          "value": int(set_id)
                        }
                      ]
                  }]
              }

    res = client.cc.search_host(kwargs)
    hosts = []
    if res.get('result', False):
        for host_info in res['data']['info']:
            hosts.append({
                "ip": host_info['host']['bk_host_innerip'],
                "os": host_info['host']["bk_os_name"],
                "host_id": host_info['host']["bk_host_id"],
                "name": host_info['host']['bk_host_name'],
                "cloud_id": host_info['host']["bk_cloud_id"][0]["id"]
            })
    else:
        logger.error(u'查询主机列表失败：%s' % res.get('message'))
    return hosts


def get_set(request):
    biz_id = request.GET.get('biz_id')
    if biz_id:
        biz_id = int(biz_id)
    else:
        return JsonResponse({'result': False, 'message': "must provide biz_id to get set"})
    data = get_set_info(biz_id)
    select_data = render_to_string('home_application/home_tbody.html', {'data': data})
    return JsonResponse({"result": True, "message": "success", "data": select_data})


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


def home(request):
    data = {"biz": get_biz_info().items(),
            "set": get_set_info(2)
            }
    return render(request, 'home_application/home.html', data)


def record(request):
    return render(request, 'home_application/record.html')



