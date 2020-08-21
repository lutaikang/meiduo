from django import http
from django.core.paginator import Paginator, EmptyPage
from django.shortcuts import render
from django.views import View
# Create your views here.

from contents.utils import get_categories
from meiduo.utils.response_code import RETCODE
from .models import GoodsCategory
from .utils import get_breadcrumb


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
            sort = 'defalut'
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
        skus = category.subs.filter(sku__is_launched=True).order_by('-sales')[:2]
        hot_skus = []
        for sku in skus:
            hot_skus.append({
                'id': sku.id,
                'default_image_url': sku.default_image.url,
                'name': sku.name,
                'price': sku.price
            })
        return http.JsonResponse({'code': RETCODE.OK, 'errmsg': 'OK', 'hot_skus': hot_skus})
