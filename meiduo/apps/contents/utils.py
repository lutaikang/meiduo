from zipp import OrderedDict

from goods.models import GoodsChannel


def get_categories():
    """
    提供商品频道和分类
    :return 菜单字典
    """
    # 构建一个有序字典
    categories = OrderedDict()
    # 查询出所有频道
    channels = GoodsChannel.objects.order_by('group_id', 'sequence')
    for channel in channels:
        # 根据频道查询出频道组
        group_id = channel.group_id
        # 判断频道组在字典中是否存在
        if group_id not in categories:
            categories[group_id] = {'channels': [], 'sub_cats': []}
        # 根据频道查询出所有一级类别
        cat1 = channel.category
        categories[group_id]['channels'].append({
            'id': cat1.id,
            'name': cat1.name,
            'url': channel.url
        })
        # 根据所有一级类别查询出所有二级类别
        for cat2 in cat1.subs.all():
            cat2.sub_cats = []
            # 根据二级类别查询出所有三级类别
            for cat3 in cat2.subs.all():
                cat2.sub_cats.append(cat3)
            categories[group_id]['sub_cats'].append(cat2)

    return categories
