def get_breadcrumb(category):
    """
    获取面包屑导航
    :param category: 商品类别
    :return: 面包屑导航
    """
    breadcrumb = dict(
        cat1='',
        cat2='',
        cat3=''
    )
    if category.parent is None:
        breadcrumb['cat1'] = category
    elif category.subs.count() == 0:
        cat2 = category.parent
        breadcrumb['cat3'] = category
        breadcrumb['cat2'] = cat2
        breadcrumb['cat1'] = cat2.parent
    else:
        breadcrumb['cat2'] = category
        breadcrumb['cat1'] = category.parent

    return breadcrumb
