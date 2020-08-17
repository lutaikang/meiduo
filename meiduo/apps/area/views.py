from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.cache import cache
from django.http import JsonResponse
from django.shortcuts import render
from django.views import View
import logging

from area.models import Area
from meiduo.utils.response_code import RETCODE

logger = logging.getLogger('django')


class AreasView(View):
    """省市区三级联动"""

    def get(self, request):
        area_id = request.GET.get('area_id')
        if area_id:
            sub_data = cache.get('sub_area_' + area_id)
            if not sub_data:
                subs = []
                try:
                    parent_model = Area.objects.get(id=area_id)
                    sub_model_list = parent_model.subs.all()
                    for subs_model in sub_model_list:
                        subs.append({'id': subs_model.id, 'name': subs_model.name})
                    sub_data = {
                        'id': parent_model.id,  # 父级pk
                        'name': parent_model.name,  # 父级name
                        'subs': subs  # 父级的子集
                    }
                except Exception as e:
                    logger.error(e)
                    return JsonResponse({'code': RETCODE.DBERR, 'errmsg': '城市或区数据错误'})
                cache.set('sub_date_' + area_id, sub_data, 3600)
                # 响应市或区数据
            return JsonResponse({'code': RETCODE.OK, 'errmsg': 'OK', 'sub_data': sub_data})

        else:
            # 获取省份信息
            province_list = cache.get('province_list')
            if not province_list:
                try:
                    province_list = []
                    areas = Area.objects.filter(parent=None)
                    for area in areas:
                        province_list.append({'id': area.id, 'name': area.name})
                except Exception as e:
                    logger.error(e)
                    return JsonResponse({'code': RETCODE.DBERR, 'errmsg': '省份信息错误'})
                # 存储缓存数据
                cache.set('province_list', province_list, 3600)
            return JsonResponse({'code': RETCODE.OK, 'errmsg': 'OK', 'province_list': province_list})
