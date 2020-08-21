from django.shortcuts import render
# Create your views here.
from django.views import View

from contents.utils import get_categories
from contents.models import ContentCategory, Content


class IndexView(View):
    def get(self, request):
        """提供首页广告页面"""
        # 商品分类
        categories = get_categories()

        # 商品广告
        contents = {}
        content_categories = ContentCategory.objects.all()
        for cat in content_categories:
            contents[cat.key] = cat.content_set.filter(status=True).order_by('sequence')

        content = {
            'categories': categories,
            'contents': contents,
        }
        return render(request, 'index.html', content)
