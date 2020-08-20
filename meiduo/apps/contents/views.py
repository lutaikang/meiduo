from django.shortcuts import render
# Create your views here.
from django.views import View

from contents.utils import get_categories


class IndexView(View):
    def get(self, request):
        """提供首页广告页面"""

        categories = get_categories()
        content = {
            'categories': categories,
        }
        return render(request, 'index.html', content)
