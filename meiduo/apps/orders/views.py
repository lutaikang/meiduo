from decimal import Decimal

from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render

# Create your views here.
from django.views import View
from django_redis import get_redis_connection
from redis import Redis

from goods.models import SKU
from users.models import Address


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
            'freight': freight,
            'payment_amount': total_amount + freight
        }

        return render(request, 'place_order.html', context)
