import base64
import json
import pickle

from django import http
from django.shortcuts import render, redirect
from django.urls import reverse
from django.views import View
# noinspection PyMethodMayBeStatic
from django_redis import get_redis_connection
from redis.client import Pipeline

from goods.models import SKU
from meiduo.utils.response_code import RETCODE


# Create your views here.


# noinspection DuplicatedCode,PyBroadException,PyMethodMayBeStatic
class CartsView(View):
    """购物车管理"""

    def get(self, request):
        """展示购物车"""
        user = request.user
        if user.is_authenticated:
            # 用户已登录查询redis购物车
            redis_conn = get_redis_connection('carts')
            redis_card = redis_conn.hgetall('carts_%s' % user.id)
            cart_selected = redis_conn.smembers('selected_%s' % user.id)
            carts_dict = {}
            for sku_id, count in redis_card.items():
                carts_dict[int(sku_id)] = {
                    'count': count,
                    'selected': sku_id in cart_selected,
                }
        else:
            # 用户未登录查询cookie购物车
            carts_str = request.COOKIE.get('carts')
            if carts_str:
                carts_dict = pickle.loads(base64.b64decode(carts_str.encode()))
            else:
                carts_dict = {}

        sku_ids = carts_dict.keys()
        skus = SKU.objects.filter(id__in=sku_ids)
        cart_skus = []
        for sku in skus:
            cart_skus.append({
                'id': sku.id,
                'name': sku.name,
                'count': carts_dict[sku.id]['count'],
                'selected': str(carts_dict.get(sku.id).get('selected')),
                'default_image_url': sku.default_image.url,
                'price': str(sku.price),
                'amount': str(sku.price * carts_dict.get(sku.id).get('selected'))
            })
        context = {
            'cart_skus': cart_skus
        }
        return render(request, 'cart.html', context)

    def post(self, request):
        """添加购物车数据"""
        # 接收检验参数
        json_dict = json.loads(request.body)
        sku_id = json_dict.get('sku_id')
        count = json_dict.get('count')
        selected = json_dict.get('selected')

        if not all([sku_id, count]):
            return http.HttpResponseForbidden('缺少必传参数')

        try:
            SKU.objects.get(id=sku_id)
        except SKU.DoesNotExist:
            return http.HttpResponseNotFound('该商品不存在')

        # noinspection PyBroadException
        try:
            count = int(count)
        except Exception:
            return http.HttpResponseForbidden('参数有误')
        if selected:
            if not isinstance(selected, bool):
                return http.HttpResponseForbidden('参数有误')

        # 判断用户是否登录
        user = request.user
        if user.is_authenticated:
            # 用户已经登录，操作redis购物车
            redis_conn = get_redis_connection('carts')
            pl: Pipeline = redis_conn.pipeline()
            pl.hincrby('carts_%s' % user.id, sku_id, count)
            if selected:
                pl.sadd('selected_%s' % user.id, sku_id)
            pl.execute()
            return http.JsonResponse({'code': RETCODE.OK, 'errmsg': '添加购物车成功'})
        else:
            # 用户未登录，操作cookie购物车
            cart_str = request.COOKIE.get("carts")
            if cart_str:
                carts_dict = pickle.loads(base64.b16decode(cart_str.encode()))
            else:
                carts_dict = {}

            if sku_id in carts_dict:
                origin_count = carts_dict[sku_id]['count']
                count = origin_count + count
            carts_dict[sku_id] = {
                'count': count,
                'select': selected
            }
            # 将字典转成bytes, 再将字节转换成base64的bytes, 最后将bytes转成字符串。
            cookie_card_str = base64.b64encode(pickle.dumps(carts_dict)).decode()
            response = http.JsonResponse({'code': RETCODE.OK, 'errmsg': '添加购物车成功'})
            response.set_cookie('carts', cookie_card_str)
            return response

    def put(self, request):
        """修改购物车"""
        carts_dict = json.loads(request.body)
        sku_id = carts_dict.get('sku_id')
        count = carts_dict.get('count')
        selected = carts_dict.get('selected')

        if not all([sku_id, count]):
            return http.HttpResponseForbidden('缺少必传参数')

        try:
            sku = SKU.objects.get(id=sku_id)
        except SKU.DoesNotExist:
            return http.HttpResponseNotFound('该商品不存在')

        try:
            count = int(count)
        except Exception:
            return http.HttpResponseForbidden('参数错误')

        if selected:
            if not isinstance(selected, bool):
                return http.HttpResponseForbidden('参数错误')

        user = request.user
        if user.is_authenticated:
            redis_conn = get_redis_connection('carts')
            pl = redis_conn.pipeline

            pl.hset('carts_%s' % user.id, sku_id, count)

            if selected:
                pl.sadd('selected_%s' % user.id, sku_id)
            else:
                pl.srem('selected_%s' % user.id, sku_id)
            pl.execute()

            cart_sku = {
                'id': sku_id,
                'count': count,
                'selected': selected,
                'name': sku.name,
                'default_image_url': sku.default_image.url,
                'price': sku.price,
                'amount': sku.price * count
            }
            return http.JsonResponse({'code': RETCODE.OK, 'errmsg': '修改购物车成功', 'cart_sku': cart_sku})
        else:
            carts_str = request.COOKIE.get('carts')
            if carts_str:
                carts_dict = pickle.loads(base64.b64decode(carts_str.encode()))
            else:
                carts_dict = {}
            carts_dict[sku_id] = {
                'count': count,
                'selected': selected,
            }
            cookie_cart_str = base64.b64encode(pickle.dumps(carts_dict)).decode()

            # 创建响应对象
            cart_sku = {
                'id': sku_id,
                'count': count,
                'selected': selected,
                'name': sku.name,
                'default_image_url': sku.default_image.url,
                'price': sku.price,
                'amount': sku.price * count,
            }
            response = http.JsonResponse({'code': RETCODE.OK, 'errmsg': '修改购物车成功', 'cart_sku': cart_sku})
            # 响应结果并将购物车数据写入到cookie
            response.set_cookie('carts', cookie_cart_str, )
            return response

    def delete(self, request):
        """删除"""
        json_dicr = json.loads(request.body)
        sku_id = json_dicr.get('sku_id')

        try:
            sku = SKU.objects.get(id=sku_id)
        except SKU.DoesNotExist:
            return http.HttpResponseNotFound('商品不存在')

        user = request.user
        if user.is_authenticated:
            redis_conn = get_redis_connection('carts')
            pl = redis_conn.pipeline
            pl.hdel('carts_%s' % user.id, sku_id)
            pl.srem('selected_%s' % user.id, sku_id)
            pl.execute()
            return http.JsonResponse({'code': RETCODE.OK, 'errmsg': '删除购物车成功'})
        else:
            carts_str = request.COOKIE.get('carts')
            if carts_str:
                carts_dict = pickle.loads(base64.b64decode(carts_str.encode()))
            else:
                carts_dict = {}
            if sku_id in carts_dict:
                del carts_dict[sku_id]
            cookie_cart_str = base64.b64decode(pickle.dumps(carts_dict))
            response = http.JsonResponse({'code': RETCODE.OK, 'errmsg': '删除购物车成功'})
            response.set_cookie('carts', cookie_cart_str)

            return response


class CartsSelectAllView(View):
    """全选购物车"""

    # noinspection PyMethodMayBeStatic
    def put(self, request):
        json_dict = json.loads(request.body)
        selected = json_dict.get('selected', True)

        if selected:
            if not isinstance(selected, bool):
                return http.HttpResponseForbidden('参数有误')

        # 判断用户是否登录
        user = request.user
        if user.is_authenticated:
            # 操作redis购物车
            redis_conn = get_redis_connection('carts')
            carts = redis_conn.hgetall('carts_%s' % user.id)
            sku_id_list = carts.keys()
            if selected:
                redis_conn.sadd('selected_%s' % user.id, *sku_id_list)
            else:
                redis_conn.srem('selected_%s' % user.id, *sku_id_list)
            return http.JsonResponse({'code': RETCODE.OK, 'errmsg': '全选购物车成功'})
        else:
            carts_str = request.COOKIE.get('carts')
            response = http.JsonResponse({'code': RETCODE.OK, 'errmsg': '全选购物车成功'})

            if carts_str:
                cart = pickle.loads(base64.b64decode(carts_str.encode()))
                for sku_id in cart.keys():
                    cart[sku_id]['selected'] = selected
                    cookie_cart = base64.b64encode(pickle.dumps(cart)).decode()
                    response.set_cookie('carts', cookie_cart)

            return response


class CartsSimpleView(View):
    """展示简略版购物车信息"""
    def get(self, request):
        user = request.user
        if user.is_authenticated:
            cart_dict = {}
            redis_conn = get_redis_connection('carts')
            cart_redis_dict = redis_conn.pipeline('carts_%s' % user.id)
            selected = redis_conn.smembers('selected_%s' % user.id)
            for sku_id, count in cart_redis_dict.items():
                cart_dict[int(sku_id)] = {
                    'count': count,
                    'selected': sku_id in selected,
                }
        else:
            carts = request.COOKIE.get('carts')
            if carts:
                cart_dict = pickle.loads(base64.b64decode(carts.encode()))
            else:
                cart_dict = {}

        cart_skus = []
        sku_ids = cart_dict.items()
        skus = SKU.objects.filter(id__in=sku_ids)
        for sku in skus:
            cart_skus.append({
                'id': sku.id,
                'name': sku.name,
                'count': cart_dict[sku.id]['count'],
                'default_image_url': sku.default_image.url
            })

        # 响应json列表数据
        return http.JsonResponse({'code': RETCODE.OK, 'errmsg': 'OK', 'cart_skus': cart_skus})
