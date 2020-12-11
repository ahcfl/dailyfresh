# 使用celery
import time
from celery import Celery
from django.conf import settings
from django.core.mail import send_mail
from django.template import loader, RequestContext

# 在任务处理者一端加这几句加载配置文件初始化
import os
# import django
# os.environ.setdefault("DJANGO_SETTINGS_MODULE", "dailyfresh.settings")
# django.setup()

from goods.models import GoodsType,IndexGoodsBanner,IndexPromotionBanner,IndexTypeGoodsBanner
from django_redis import get_redis_connection

# 创建一个Celery类的实例对象  第一个参数是启动之后app对应的名字可随意指定(一般默认是任务路径)
# 第二个参数是中间人(broker://ip:port/第几个数据库)
app = Celery('celery_tasks.tasks', broker='redis://192.168.182.132:6379/8')

# 定义任务函数 --> 到用户点击注册时候, celery接收到发送邮件的task--> broker <--work一方的task就会接收到,然后调用函数执行
# 使用task方法对函数进行装饰


@app.task
def send_register_active_email(to_email, username, token):
    """ 发送给用户邮件并激活 """
    # 组织邮件信息
    subject = '天天生鲜欢迎信息'  # 主题
    message = ''  # 包含html标签要使用 html_message 发送正文
    sender = settings.EMAIL_FROM  # 发件人
    receiver = [to_email]  # 收件人的邮箱
    # 前面四个是固定按照位置传递的参数, html_message是指定的参数
    html_message = '<h1>%s, 欢迎您成为天天生鲜的注册会员</h1>请点击下面链接激活您的账户<br/><a href="http://192.168.182.132/user/active/%s">http://192.168.182.132/user/active/%s</a>' % (
    username, token, token)
    # smtp服务器
    send_mail(subject, message, sender, receiver, html_message=html_message)
    # 演示即使睡眠5s发送 , 也不延迟加载goods首页, 异步执行
    # time.sleep(5)


@app.task
def generate_static_index_html():
    '''产生首页静态页面'''
    # 获取商品的种类信息
    types = GoodsType.objects.all()

    # 获取首页轮播商品信息
    goods_banners = IndexGoodsBanner.objects.all().order_by('index')

    # 获取首页促销活动信息
    promotion_banners = IndexPromotionBanner.objects.all().order_by('index')

    # 获取首页分类商品展示信息
    for type in types:  # GoodsType
        # 获取type种类首页分类商品的图片展示信息
        image_banners = IndexTypeGoodsBanner.objects.filter(type=type, display_type=1).order_by('index')
        # 获取type种类首页分类商品的文字展示信息
        title_banners = IndexTypeGoodsBanner.objects.filter(type=type, display_type=0).order_by('index')

        # 动态给type增加属性，分别保存首页分类商品的图片展示信息和文字展示信息
        type.image_banners = image_banners
        type.title_banners = title_banners

    # 组织模板上下文
    context = {'types': types,
               'goods_banners': goods_banners,
               'promotion_banners': promotion_banners}

    # 使用模板
    # 1.加载模板文件,返回模板对象
    temp = loader.get_template('static_index.html')
    # 2.模板渲染
    static_index_html = temp.render(context)

    # 生成首页对应静态文件  BASE_DIR就是项目的目录
    save_path = os.path.join(settings.BASE_DIR, 'static/index.html')
    with open(save_path, 'w') as f:
        f.write(static_index_html)


