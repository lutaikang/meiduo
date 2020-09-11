import datetime
import json
import logging

from django import http
from django.core.paginator import Paginator, EmptyPage
from django.shortcuts import render, get_object_or_404
from django.views import View
# Create your views here.
from django.views.generic import DetailView
from django_redis import get_redis_connection

from contents.utils import get_categories
from meiduo.utils.response_code import RETCODE
from meiduo.utils.views import LoginRequiredJSONMixin
from .models import GoodsCategory, SKU, GoodsVisitCount
from .utils import get_breadcrumb

logger = logging.getLogger('django')


class ListView(View):
    """商品列表页面"""

    def get(self, request, category_id, page_num):
        # 根据category_id查询出商品类别
        try:
            category = GoodsCategory.objects.get(id=category_id)
        except GoodsCategory.DoesNotExist:
            return http.HttpResponseNotFound('GoodsCategory does not exist')

        # 查询商品频道分类
        categories = get_categories()

        # 查询面包屑导航
        breadcrumb = get_breadcrumb(category)

        # 列表页分页和排序
        sort = request.GET.get('sort', 'default')
        if sort == 'price':
            sort_filed = 'price'
        elif sort == 'hot':
            sort_filed = '-sales'
        else:
            sort = 'default'
            sort_filed = 'ctime'
        # 查询出该类别的所有上架的商品数据
        skus = category.sku_set.filter(is_launched=True).order_by(sort_filed)
        # 创建分页器
        paginator = Paginator(skus, 5)
        try:
            page_skus = paginator.page(page_num)
        except EmptyPage:
            # 如果page_num不正确，默认给用户404
            return http.HttpResponseNotFound('empty page')
        # 获取列表页总页数
        total_page = paginator.num_pages

        # 渲染页面
        content = {
            'categories': categories,  # 频道分类
            'breadcrumb': breadcrumb,  # 面包屑导航
            'sort': sort,  # 排序字段
            'category': category,  # 第三级分类
            'category_id': category_id,
            'page_skus': page_skus,  # 分页后的数据
            'total_page': total_page,  # 总页数
            'page_num': page_num,  # 当前页码
        }

        return render(request, 'list.html', content)


class HotGoodsView(View):
    """列表页热销排行"""

    def get(self, request, category_id):
        # 根据category_id 查出商品类别
        try:
            category = GoodsCategory.objects.get(id=category_id)
        except GoodsCategory.DoesNotExist:
            return http.JsonResponse({'code': RETCODE.DBERR, 'errmsg': 'GoodsCategory does not exist'})
        skus = category.sku_set.filter(is_launched=True).order_by('-sales')[:2]
        hot_skus = []
        for sku in skus:
            hot_skus.append({
                'id': sku.id,
                'default_image_url': sku.default_image.url,
                'name': sku.name,
                'price': sku.price
            })
        return http.JsonResponse({'code': RETCODE.OK, 'errmsg': 'OK', 'hot_skus': hot_skus})


class GoodsDetailView(DetailView):
    """商品详情页面"""
    template_name = 'detail.html'
    context_object_name = 'sku'
    model = SKU

    def get(self, request, *args, **kwargs):
        try:
            return super().get(self, request, *args, **kwargs)
        except SKU.DoesNotExist:
            return render(self.request, '404.html')
        # return super().get(self, request, *args, **kwargs)

    def get_object(self, queryset=None):
        sku_id = self.kwargs.get('sku_id')
        queryset = self.get_queryset()
        try:
            sku = queryset.get(id=sku_id)
        except SKU.DoesNotExist as e:
            raise e
        return sku

    def get_context_data(self, **kwargs):
        # 查询商品频道分类
        categories = get_categories()
        # 查询面包屑导航
        breadcrumb = get_breadcrumb(self.object.category)
        # 构建当前商品的规格键
        sku_specs = self.object.specs.order_by('spec_id')
        sku_key = []
        for spec in sku_specs:
            sku_key.append(spec.option.id)
        # 获取当前商品的所有sku
        skus = self.object.spu.sku_set.all()
        # 构建不同规格参数（选项）的sku字典
        spec_sku_map = {}
        for s in skus:
            # 获取sku的规格参数
            s_specs = s.specs.order_by('spec_id')
            # 用于形成规格参数sku字典的键
            key = []
            for spec in s_specs:
                key.append(spec.option.id)
            # 向规格参数sku字典添加记录
            spec_sku_map[tuple(key)] = s.id
        # 获取当前商品的规格信息
        goods_specs = self.object.spu.specs.order_by('id')
        # 若当前的sku的规格信息不完整，则不再继续
        if len(sku_key) < len(goods_specs):
            return
        for index, spec in enumerate(goods_specs):
            # 复制当前的sku的规格键
            key = sku_key[:]
            # 该规格选项
            spec_options = spec.options.all()
            for option in spec_options:
                # 在规格参数sku字典中查找符合当前规格的sku
                key[index] = option.id
                option.sku_id = spec_sku_map.get(tuple(key))
            spec.spec_options = spec_options

        context = super().get_context_data(**kwargs)
        context['categories'] = categories
        context['breadcrumb'] = breadcrumb
        context['specs'] = goods_specs
        # context = {
        #     'categories': categories,
        #     'breadcrumb': breadcrumb,
        #     'sku': self.object,
        # }
        return context


class DetailVisitView(View):
    """详情页分类商品访问量"""

    def post(self, request, category_id):
        """记录分类商品访问量"""
        try:
            category = GoodsCategory.objects.get(id=category_id)
        except GoodsCategory.DoesNotExist:
            return http.HttpResponseForbidden('查询不到该类别商品')

        # 获取今天日期
        # t = datetime.datetime.timezone()
        # today_str = '%d-%02d-%02d' % (t.year, t.month, t.day)
        # today_date = datetime.datetime.strptime(today_str, '%Y-%m-%d')
        today_date = datetime.date.today()
        try:
            counts_data = category.goodsvisitcount_set.get(date=today_date)
        except GoodsVisitCount.DoesNotExist:
            counts_data = GoodsVisitCount()

        try:
            counts_data.category = category
            counts_data.count += 1
            counts_data.save()
        except Exception as e:
            logger.error(e)
            return http.HttpResponseServerError('服务器异常')
        # logger.error(1)
        return http.JsonResponse({'code': RETCODE.OK, 'errmsg': 'OK'})


class UserBrowseHistory(LoginRequiredJSONMixin, View):
    """用户浏览记录"""

    def get(self, request):
        """获取用户浏览记录"""
        user_id = request.user.id
        redis_conn = get_redis_connection('history')
        sku_list = redis_conn.lrange('history_%s' % user_id, 0, -1)
        skus = []
        for sku_id in sku_list:
            sku = SKU.objects.get(id=sku_id)
            print(sku_id)   # 字节类型数据json不能进行序列化
            skus.append({
                'id': sku.id,
                'name': sku.name,
                'default_image_url': sku.default_image.url,
                'price': sku.price
            })
        return http.JsonResponse({'code': RETCODE.OK, 'errmsg': 'ok', 'skus': skus})

    def post(self, request):
        """保存用户浏览记录"""
        json_dict = json.loads(request.body.decode())
        sku_id = json_dict.get('sku_id')

        try:
            sku = SKU.objects.get(id=sku_id)
        except SKU.DoesNotExist:
            return http.HttpResponseForbidden('sku不存在')

        redis_conn = get_redis_connection('history')
        pl = redis_conn.pipeline()
        user_id = request.user.id

        pl.lrem('history_%s' % user_id, 0, sku_id)
        pl.lpush('history_%s' % user_id, sku_id)
        pl.ltrim('history_%s' % user_id, 0, 4)
        pl.execute()

        return http.JsonResponse({'code': RETCODE.OK, 'errmsg': 'ok'})
