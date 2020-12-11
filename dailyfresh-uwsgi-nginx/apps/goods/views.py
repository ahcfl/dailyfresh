from django.shortcuts import render, redirect
from django.core.urlresolvers import reverse
from django.views.generic import View
from django.core.cache import cache
from django.core.paginator import Paginator
from goods.models import GoodsType, GoodsSKU, IndexGoodsBanner,IndexPromotionBanner,IndexTypeGoodsBanner
from django_redis import get_redis_connection
from order.models import OrderGoods
# Create your views here.

# class Test(object):
#     def __init__(self):
#         self.name = 'abc'
# 动态增加属性
# t = Test()
# t.age = 10
# print(t.age)


# http://127.0.0.1:8000 动态展示首页商品 celery生成静态页面
class IndexView(View):
    '''首页'''
    def get(self, request):
        '''显示首页'''

        # 尝试从缓存中获取数据 --> 获得不到返回None
        context = cache.get('index_page_data')

        if context is None:
            print('第一次访问--->设置缓存')
            # 缓存中没有数据
            # 1.获取商品的种类信息
            types = GoodsType.objects.all()

            # 2.获取首页轮播商品信息
            goods_banners = IndexGoodsBanner.objects.all().order_by('index')

            # 3.获取首页促销活动信息
            promotion_banners = IndexPromotionBanner.objects.all().order_by('index')

            # 4.获取首页分类商品展示信息
            for type in types: # GoodsType
                # 获取type种类首页分类商品的图片展示信息
                image_banners = IndexTypeGoodsBanner.objects.filter(type=type, display_type=1).order_by('index')
                # 获取type种类首页分类商品的文字展示信息
                title_banners = IndexTypeGoodsBanner.objects.filter(type=type, display_type=0).order_by('index')

                # 动态给type增加属性，分别保存首页分类商品的图片展示信息和文字展示信息
                type.image_banners = image_banners
                type.title_banners = title_banners

            context = {'types': types,
                       'goods_banners': goods_banners,
                       'promotion_banners': promotion_banners}

            # 设置缓存 有时，缓存整个页面不会让你获益很多，事实上，过度的矫正原来的不方便，变得更加不方便。
            # Django提供了一个底层的 cache API. 你可以用这个 API来储存在缓存中的对象，并且控制粒度随你喜欢
            # 您可以缓存可以安全pickle的任何Python对象：模型对象的字符串，字典，列表等等。
            # 最基本的接口是 set(key, value, timeout) 和 get(key):
            # key  value timeout
            cache.set('index_page_data', context, 3600)

        # 5.获取用户购物车中商品的数目
        user = request.user
        cart_count = 0
        if user.is_authenticated():
            # 用户已登录
            conn = get_redis_connection('default')
            cart_key = 'cart_%d' % user.id
            cart_count = conn.hlen(cart_key)

        # 组织模板上下文  调用字典的update方法更新
        context.update(cart_count=cart_count)

        # 使用模板
        return render(request, 'index.html', context)


# /goods/商品id
class DetailView(View):
    '''详情页'''
    def get(self, request, goods_id):
        '''显示详情页'''
        # 1.捕获skuID是否存在
        try:
            sku = GoodsSKU.objects.get(id=goods_id)
        except GoodsSKU.DoesNotExist:
            # 商品不存在 --> 跳转到商品首页
            return redirect(reverse('goods:index'))

        # 2.获取商品的分类信息
        types = GoodsType.objects.all()

        # 3.获取商品的评论信息  排除空评论
        sku_orders = OrderGoods.objects.filter(sku=sku).exclude(comment='')

        # 3.获取新品信息  type=sku.type
        #  create_time = models.DateTimeField(auto_now_add=True, verbose_name='创建时间') 最新创建的降序获取
        new_skus = GoodsSKU.objects.filter(type=sku.type).order_by('-create_time')[:2]

        # 4.获取同一个SPU的其他规格商品
        same_spu_skus = GoodsSKU.objects.filter(goods=sku.goods).exclude(id=goods_id)

        # 5.获取用户购物车中商品的数目
        user = request.user
        cart_count = 0
        if user.is_authenticated():
            # 用户已登录
            # 获取购物车里的数目
            conn = get_redis_connection('default')
            cart_key = 'cart_%d' % user.id
            cart_count = conn.hlen(cart_key)

            # 添加用户的历史记录
            conn = get_redis_connection('default')
            history_key = 'history_%d'%user.id
            # 移除列表中的goods_id
            conn.lrem(history_key, 0, goods_id)
            # 把goods_id插入到列表的左侧
            conn.lpush(history_key, goods_id)
            # 只保存用户最新浏览的5条信息
            conn.ltrim(history_key, 0, 4)

        # 组织模板上下文
        context = {'sku':sku, 'types':types,
                   'sku_orders':sku_orders,
                   'new_skus':new_skus,
                   'same_spu_skus':same_spu_skus,
                   'cart_count':cart_count}

        # 使用模板
        return render(request, 'detail.html', context)


# 种类id 页码 排序方式
# restful api -> 请求一种资源
# /list?type_id=种类id&page=页码&sort=排序方式
# /list/种类id/页码/排序方式
# /list/种类id/页码?sort=排序方式
class ListView(View):
    '''列表页'''
    def get(self, request, type_id, page):
        '''显示列表页'''

        # 1.获取种类信息
        try:
            type = GoodsType.objects.get(id=type_id)
        except GoodsType.DoesNotExist:
            # 种类不存在
            return redirect(reverse('goods:index'))

        # 2.获取商品的分类信息
        types = GoodsType.objects.all()

        # 3.获取排序的方式 # 获取分类商品的信息
        # sort=default 按照默认id排序
        # sort=price 按照商品价格排序
        # sort=hot 按照商品销量排序
        sort = request.GET.get('sort')

        if sort == 'price':
            skus = GoodsSKU.objects.filter(type=type).order_by('price')
        elif sort == 'hot':
            skus = GoodsSKU.objects.filter(type=type).order_by('-sales')
        else:
            sort = 'default'
            skus = GoodsSKU.objects.filter(type=type).order_by('-id')

        # 4.对数据进行分页 Django提供了一些类来帮助你管理分页的数据
        #  -- 也就是说，数据被分在不同页面中，并带有“上一页/下一页”标签。这些类位于django/core/paginator.py中。
        paginator = Paginator(skus, 1)

        # 4.1获取第page页的内容, 并作容错处理
        try:
            page = int(page)
        except Exception as e:
            page = 1
        # 4.2页面总数 属性
        if page > paginator.num_pages:
            page = 1

        # 4.3获取第page页的Page实例对象
        skus_page = paginator.page(page)

        # todo: 进行页码的控制，页面上最多显示5个页码
        # 1.总页数小于5页，页面上显示所有页码
        # 2.如果当前页是前3页，显示1-5页
        # 3.如果当前页是后3页，显示后5页
        # 4.其他情况，显示当前页的前2页，当前页，当前页的后2页
        num_pages = paginator.num_pages
        if num_pages < 5:
            pages = range(1, num_pages+1)
        elif page <= 3:
            pages = range(1, 6)
        elif num_pages - page <= 2:
            pages = range(num_pages-4, num_pages+1)
        else:
            pages = range(page-2, page+3)

        # 5.获取新品信息  切片 取前两个
        new_skus = GoodsSKU.objects.filter(type=type).order_by('-create_time')[:2]

        # 6.获取用户购物车中商品的数目
        user = request.user
        cart_count = 0
        if user.is_authenticated():
            # 用户已登录
            conn = get_redis_connection('default')
            cart_key = 'cart_%d' % user.id
            cart_count = conn.hlen(cart_key)

        # 7.组织模板上下文
        context = {'type':type, 'types':types,
                   'skus_page':skus_page,
                   'new_skus':new_skus,
                   'cart_count':cart_count,
                   'sort':sort, 'pages': pages}

        # 8.使用模板
        return render(request, 'list.html', context)















