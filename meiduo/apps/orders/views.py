import json
import logging
from decimal import Decimal

from django import http
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.paginator import Paginator, EmptyPage
from django.db import transaction
from django.shortcuts import render

# Create your views here.
from django.utils import timezone
from django.views import View
from django_redis import get_redis_connection
from redis import Redis

from goods.models import SKU
from meiduo.utils import constants
from meiduo.utils.response_code import RETCODE
from meiduo.utils.views import LoginRequiredJSONMixin
from orders.models import OrderInfo, OrderGoods
from users.models import Address

logger = logging.getLogger('django')


class OrderSettlementView(LoginRequiredMixin, View):
    """展示结算订单"""

    # noinspection PyMethodMayBeStatic
    def get(self, request):
        user = request.user
        # 查询地址信息
        try:
            addresses = Address.objects.filter(user=user, is_deleted=False)
        except Address.DoesNotExist:
            addresses = None

        redis_conn: Redis = get_redis_connection('carts')
        redis_cart = redis_conn.hgetall('carts_%s' % user.id)
        cart_selected = redis_conn.smembers('selected_%s' % user.id)

        cart = {}
        for sku_id in cart_selected:
            cart[int(sku_id)] = int(redis_cart[sku_id])

        total_count = 0
        total_amount = Decimal(0.00)
        skus = SKU.objects.filter(id__in=cart.keys())
        for sku in skus:
            sku.count = cart[sku.id]
            sku.amount = sku.count * sku.price

            total_count += sku.count
            total_amount += sku.count * sku.price

        freight = Decimal('10.00')

        context = {
            'addresses': addresses,
            'skus': skus,
            'total_count': total_count,
            'total_amount': total_amount,
            'freight': freight,
            'payment_amount': total_amount + freight
        }

        return render(request, 'place_order.html', context)


class OrderCommitView(LoginRequiredJSONMixin, View):
    """提交订单"""

    def post(self, request):
        """保存订单信息和订单商品信息"""
        json_dict = json.loads(request.body)
        address_id = json_dict.get('address_id')
        pay_method = json_dict.get('pay_method')

        if not all([address_id, pay_method]):
            return http.HttpResponseForbidden('缺少必传参数')
        try:
            address = Address.objects.get(id=address_id)
        except Exception:
            return http.HttpResponseForbidden('参数address_id错误')

        if pay_method not in [OrderInfo.PAY_METHODS_ENUM['CASH'], OrderInfo.PAY_METHODS_ENUM['ALIPAY']]:
            return http.HttpResponseForbidden('参数pay_method错误')

        user = request.user
        order_id = timezone.localtime().strftime('%Y%m%d%H%M%S') + ('%09d' % user.id)
        # 保存订单信息
        try:
            with transaction.atomic():
                # 创建事务保存点
                save_id = transaction.savepoint()

                order = OrderInfo.objects.create(
                    order_id=order_id,
                    user=user,
                    address=address,
                    total_count=0,
                    total_amount=Decimal('0'),
                    freight=Decimal('10.00'),
                    pay_method=pay_method,
                    status=OrderInfo.ORDER_STATUS_ENUM['UNPAID'] if pay_method == OrderInfo.PAY_METHODS_ENUM[
                        'ALIPAY'] else OrderInfo.ORDER_STATUS_ENUM['UNSEND']
                )

                cart = {}
                redis_conn = get_redis_connection('carts')
                redis_cart = redis_conn.hgetall('carts_%s' % user.id)
                redis_selected = redis_conn.smembers('selected_%s' % user.id)

                for sku_id in redis_selected:
                    cart[int(sku_id)] = int(redis_cart[sku_id])

                sku_ids = cart.keys()
                for sku_id in sku_ids:
                    while True:
                        sku = SKU.objects.get(id=sku_id)

                        origin_stock = sku.stock
                        origin_sales = sku.sales

                        sku_count = cart[sku_id]
                        if sku_count > origin_stock:
                            transaction.savepoint_rollback(save_id)
                            return http.JsonResponse({'code': RETCODE.STOCKERR, 'errmsg': '库存不足'})
                        # import time
                        # time.sleep(2)
                        new_stock = origin_stock - sku_count
                        new_sales = origin_sales + sku_count
                        result = SKU.objects.filter(id=sku_id, stock=origin_stock).update(stock=new_stock,
                                                                                          sales=new_sales)
                        if result == 0:
                            continue
                        sku.spu.sales += sku_count
                        sku.spu.save()

                        OrderGoods.objects.create(
                            order=order,
                            sku=sku,
                            count=sku_count,
                            price=sku.price,
                        )

                        order.total_count += sku_count
                        order.total_amount += (sku_count * sku.price)

                        break

                    order.total_amount += order.freight
                    order.save()
            # 保存订单数据成功，显式的提交一次事务
            transaction.savepoint_commit(save_id)
        except Exception as e:
            logger.error(e)
            return http.JsonResponse({'code': RETCODE.DBERR, 'errmsg': '下单失败'})

        # 清除购物车中已结算商品
        pl = redis_conn.pipeline()
        pl.hdel('carts_%s' % user.id, *redis_selected)
        pl.srem('selected_%s' % user.id, *redis_selected)
        pl.execute()
        # 响应提交订单结果
        return http.JsonResponse({'code': RETCODE.OK, 'errmsg': '下单成功', 'order_id': order.order_id})


class OrderSuccessView(LoginRequiredMixin, View):
    """提交订单成功"""

    def get(self, request):
        order_id = request.GET.get('order_id')
        payment_amount = request.GET.get('payment_amount')
        pay_method = request.GET.get('pay_method')

        context = {
            'order_id': order_id,
            'payment_amount': payment_amount,
            'pay_method': pay_method
        }
        return render(request, 'order_success.html', context)


class UserOrderInfoView(LoginRequiredMixin, View):
    """我的订单"""

    def get(self, request, page_num):
        """提供我的订单页面"""
        user = request.user
        # 查询订单
        orders = user.orderinfo_set.all().order_by('-ctime')
        # 遍历所有订单
        for order in orders:
            order.status_name = OrderInfo.ORDER_STATUS_CHOICES[order.status-1][1]
            order.pay_method_name = OrderInfo.PAY_METHOD_CHOICES[order.pay_method - 1][1]
            order.sku_list = []
            order_goods = order.skus.all()
            for order_good in order_goods:
                sku = order_good.sku
                sku.count = order_good.count
                sku.price = order_good.price
                sku.amount = sku.price * sku.count
                order.sku_list.append(sku)
        page_num = int(page_num)
        try:
            paginator = Paginator(orders, constants.ORDERS_LIST_LIMIT)
            page_orders = paginator.page(page_num)
            total_page = paginator.num_pages
        except EmptyPage:
            return http.HttpResponseNotFound('订单不存在')

        context = {
            'page_orders': page_orders,
            'total_page': total_page,
            'page_num': page_num
        }
        return render(request, "user_center_order.html", context)
