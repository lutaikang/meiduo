import os
import time

from django.conf import settings
from django.template import loader

from contents.models import ContentCategory
from contents.utils import get_categories


# noinspection DuplicatedCode
def generate_static_index_html():
    """
    生成静态的主页html文件
    """
    print('%s: generate_static_index_html' % time.ctime())
    # 获取商品频道和分类
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

    template = loader.get_template('index.html')
    html_text = template.render(content)

    file_path = os.path.join(settings.STATICFILES_DIRS[0], 'index.html')
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(html_text)


def ccc(name):
    return name


if __name__ == "__main__":
    generate_static_index_html()
