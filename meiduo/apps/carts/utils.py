import base64
import pickle

from django_redis import get_redis_connection
from redis import Redis


def merge_cart_cookie_to_redis(request, user, response):
    """
    将cookie购物车中的数据合并到redis购物车中
    :param request: 利用request获取cookie中的购物车数据
    :param user: 获取当前登录用户
    :param response: 清楚request中的cookie
    :return: 返回一个response
    """

    cart = request.COOKIES.get('carts')
    if not cart:
        return response

    cookie_cart_dict = pickle.loads(base64.b64decode(cart.encode()))

    new_cart_dict = {}
    new_cart_select_add = []
    new_cart_select_remove = []

    for sku_id in cookie_cart_dict.keys():
        new_cart_dict[sku_id] = cookie_cart_dict[sku_id]['count']

        if cookie_cart_dict[sku_id].get('selected'):
            new_cart_select_add.append(sku_id)
        else:
            new_cart_select_remove.append(sku_id)

    redis_conn: Redis = get_redis_connection('carts')
    pl = redis_conn.pipeline()

    pl.hmset('carts_%s' % user.id, new_cart_dict)

    if new_cart_select_add:
        pl.sadd('selected_%s' % user.id, *new_cart_select_add)

    if new_cart_select_remove:
        pl.srem('selected_%s' % user.id, *new_cart_select_remove)
    pl.execute()

    response.delete_cookie('carts')

    return response
