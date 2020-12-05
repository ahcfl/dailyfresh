from django.shortcuts import render, redirect
from django.core.urlresolvers import reverse
from django.contrib.auth import authenticate, login, logout
from utils.mixin import LoginRequiredMixin
from django_redis import get_redis_connection
from django.core.mail import send_mail
from django.views.generic import View
from django.http import HttpResponse
from goods.models import GoodsSKU
# 已经在setting中 --> import sys 当改变了系统查找模块的绝对路径,所以不能用app.user
from user.models import User, Address
# 引入异步执行 发送邮件函数
from celery_tasks.tasks import send_register_active_email

from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from itsdangerous import SignatureExpired
from django.conf import settings
import re

# Create your views here.


# /user/register
def register(request):
    """ 显示注册页面 """
    if request.method == 'GET':
        return render(request, 'register.html')
    else:
        # 进行注册处理
        # 1. 接收浏览器的request数据
        username = request.POST.get('user_name')
        password = request.POST.get('pwd')
        email = request.POST.get('email')
        # 如果用户同意 勾选--> checkbox传回来值为on
        allow = request.POST.get('allow')

        # 2. 进行数据的校验--> all([])函数内参数全部为真-->为真
        # 2.1 当数据不完整
        if not all([username, password, email]):
            return render(request, 'register.html', {'errmsg': '您的信息不完整!'})
        # 2.2 校验邮箱
        if not re.match(r'^[a-z0-9][\w.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', email):
            return render(request, 'register.html', {'errmsg': '您的邮箱格式不正确!'})
        # 2.3 是否同意用户协议
        if allow != 'on':
            return render(request, 'register.html', {'errmsg': '请同意协议,才可使用哦!'})

        # 2.4 校验用户名是否重复 --> 先从数据库查找,再判断,没有返回None
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            # 如果不存在,抛出异常,赋值None
            user = None

        if user:
            # 用户名已经存在
            return render(request, 'register.html', {'errmsg': '用户名已存在!'})

        # 3. 业务处理--> 进行用户的注册
        # 一般过程的数据存储
        # user = User()
        # user.username = username
        # user.password = password
        # user.save()
        # 使用django内置方法 认证注册 注意参数顺序
        user = User.objects.create_user(username, email, password)
        # django内置方法 直接默认激活
        user.is_active = 0
        user.save()

        # 4. 返回应答 --> 注册成功, 跳转到商品首页
        return redirect(reverse('goods:index'))


# /user/register_handle
def register_handle(request):
    """ 用户注册处理 """

    # 1. 接收浏览器的request数据
    username = request.POST.get('user_name')
    password = request.POST.get('pwd')
    email = request.POST.get('email')
    # 如果用户同意 勾选--> checkbox传回来值为on
    allow = request.POST.get('allow')

    # 2. 进行数据的校验--> all([])函数内参数全部为真-->为真
    # 2.1 当数据不完整
    if not all([username, password, email]):

        return render(request, 'register.html', {'errmsg': '您的信息不完整!'})
    # 2.2 校验邮箱
    if not re.match(r'^[a-z0-9][\w.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', email):
        return render(request, 'register.html', {'errmsg': '您的邮箱格式不正确!'})
    # 2.3 是否同意用户协议
    if allow != 'on':
        return render(request, 'register.html', {'errmsg': '请同意协议,才可使用哦!'})

    # 2.4 校验用户名是否重复 --> 先从数据库查找,再判断,没有返回None
    try:
        user = User.objects.get(username=username)
    except User.DoesNotExist:
        # 如果不存在,抛出异常,赋值None
        user = None

    if user:
        # 用户名已经存在
        return render(request, 'register.html', {'errmsg': '用户名已存在!'})

    # 3. 业务处理--> 进行用户的注册
    # 一般过程的数据存储
    # user = User()
    # user.username = username
    # user.password = password
    # user.save()
    # 3.1 使用django内置方法 认证注册 注意参数顺序
    user = User.objects.create_user(username, email, password)
    # django内置方法 直接默认激活
    user.is_active = 0
    user.save()

    # 3.2 发送激活邮件,包含激活链接: http://127.0.0.1:8000/user/active/3(userID)
    # 3.2.1 激活链接 需要包含用户的身份信息,并且要把身份信息进行加密
    # 加密用户的身份信息,生成激活的token--> 这里直接使用django自动生成的密钥
    serializer = Serializer(settings.SECRET_KEY, 3600)
    info = {'confirm': user.id}
    token = serializer.dumps(info)
    # 3.2.2 发邮件
    subject = '天天生鲜欢迎信息'    # 主题
    message = '邮件正文'
    sender = settings.EMAIL_FROM    # 发件人
    receiver = [email]      # 收件人的邮箱
    send_mail(subject, message, sender, receiver)

    # 4. 返回应答 --> 注册成功, 跳转到商品首页
    return redirect(reverse('goods:index'))


# 基于类的视图提供另一种将视图实现为 Python 对象而不是函数的方法。
# /user/register
class RegisterView(View):
    """ (基于类的注册视图) """
    def get(self, request):
        """ 显示注册页面 """
        return render(request, 'register.html')

    def post(self, request):
        """ 注册处理 """
        # 1. 接收浏览器的request数据
        username = request.POST.get('user_name')
        password = request.POST.get('pwd')
        email = request.POST.get('email')
        # 如果用户同意 勾选--> checkbox传回来值为on
        allow = request.POST.get('allow')

        # 2. 进行数据的校验--> all([])函数内参数全部为真-->为真
        # 2.1 当数据不完整
        if not all([username, password, email]):
            return render(request, 'register.html', {'errmsg': '您的信息不完整!'})
        # 2.2 校验邮箱
        if not re.match(r'^[a-z0-9][\w.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', email):
            return render(request, 'register.html', {'errmsg': '您的邮箱格式不正确!'})
        # 2.3 是否同意用户协议
        if allow != 'on':
            return render(request, 'register.html', {'errmsg': '请同意协议,才可使用哦!'})

        # 2.4 校验用户名是否重复 --> 先从数据库查找,再判断,没有返回None
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            # 如果不存在,抛出异常,赋值None
            user = None

        if user:
            # 用户名已经存在
            return render(request, 'register.html', {'errmsg': '用户名已存在!'})

        # 3. 业务处理--> 进行用户的注册
        # 一般过程的数据存储
        # user = User()
        # user.username = username
        # user.password = password
        # user.save()
        # 3.1 使用django内置方法 认证注册 注意参数顺序
        user = User.objects.create_user(username, email, password)
        # django内置方法 直接默认激活
        user.is_active = 0
        user.save()

        # 3.2 发送激活邮件,包含激活链接: http://127.0.0.1:8000/user/active/3(userID)

        # 3.2.1 激活链接 需要包含用户的身份信息,并且要把身份信息进行加密
        # 加密用户的身份信息,生成激活的token--> 这里直接使用django自动生成的密钥
        serializer = Serializer(settings.SECRET_KEY, 3600)
        info = {'confirm': user.id}
        token = serializer.dumps(info)      # 加密后返回的token是bytes格式
        token = token.decode()          # 解码成字符串的格式

        # 3.2.2 发邮件
        # 要使得程序到这里不阻塞,能直接加载首页--> 设置celery异步执行 --> 经过app.task装饰后--> 使用delay()函数把发送邮件放入任务队列
        send_register_active_email.delay(email, username, token)

        # 4. 返回应答 --> 注册成功, 跳转到商品首页
        return redirect(reverse('goods:index'))


# /user/active
class ActiveView(View):
    """ 用户激活 """
    def get(self, request, token):
        """ 进行用户激活 """
        # 1. 进行解密, 获取激活的用户信 首先要有解密的对象,和加密时的参数
        serializer = Serializer(settings.SECRET_KEY, 3600)
        try:
            info = serializer.loads(token)      # 加密进去的是什么,解密的就是什么
            # 2. 获取待激活用户的id
            use_id = info['confirm']
            # 3. 根据id获取用户信息
            user = User.objects.get(id=use_id)
            # 4. 激活
            user.is_active = 1
            user.save()
            # 5. 跳转到登录页面
            return redirect(reverse('user:login'))
        except SignatureExpired as e:
            # 1. 如果激活链接expired  生成的token里加密的时间已经进去了,所以在这可以判断是否过期
            return HttpResponse('激活链接已过期!')


# /user/login
class LoginView(View):
    """ 登录 """
    def get(self, request):
        """ 显示登录页面 """
        # 判断用户登录是是否记住用户名
        if 'username' in request.COOKIES:
            username = request.COOKIES.get('username')
            checked = 'checked'
        else:
            username = ''
            checked = ''

        # 使用模板
        return render(request, 'login.html', {'username': username, 'checked': checked})

    def post(self, request):
        """ 登录校验 """
        # 1. 接收数据
        username = request.POST.get('username')
        password = request.POST.get('pwd')
        # 2. 校验数据
        if not all([username, password]):
            return render(request, 'login.html', {'errmsg': '数据不完整!'})

        # 3. 业务处理:登录校验
        # 普通校验
        # user = User.objects.get(username=username, password=password)

        # 3.1 现在使用 django内置认证验证方法  authenticate自动认证输入的密码是否匹配给定的用户
        # 1) 如果后端验证有效:则返回一个class:django.contrib.auth.models.User
        # 2) 如果后端引发 PermissionDenied 错误: 返回 None
        user = authenticate(username=username, password=password)
        if user is not None:
            # 3.2 A backend authenticated the credentials 用户已激活
            if user.is_active:
                # 3.2.1 记录用户的登录状态
                # 从视图中登入一个用户，请使用login()。它接受一个HttpRequest对象和一个User对象。login()
                # 使用Django的会话框架保存用户的ID在会话中。
                login(request, user)

                # 默认跳转到首页
                # 获取登录后要跳转到的页面地址 login_required()认证返回的url
                # 如果用户没有登入，则重定向到settings.LOGIN_URL(/url/login),并将当前访问的绝对路径传递到查询字符串中
                # 如果用户已经登入，则正常执行视图. 视图的代码可以安全地假设用户已经登入
                next_url = request.GET.get('next', reverse('goods:index'))  # 获取不到返回None,使用后面的默认地址
                # 获得到next,跳转到next_url
                # HttpResponseRedirect的子类 创建设置cookie的对象
                response = redirect(next_url)

                # 3.2.2 判断是否需要记住用户名
                remember = request.POST.get('remember')
                if remember == 'on':
                    # 记住用户名 --> 用响应类的对象调用set_cookie() 创建cookie
                    response.set_cookie('username', username, max_age=7*24*3600)
                else:
                    response.delete_cookie('username')

                # 返回应答 --> 跳转到首页
                return response
            else:
                # 用户未激活
                return render(request, 'login.html', {'errmsg': '账户未激活!'})
        else:
            # 3.3 No backend authenticated the credentials 用户名或密码错误
            return render(request, 'login.html', {'errmsg': '用户名或密码错误!'})


# /user/logout
class LogoutView(View):
    """ 退出登录 """
    def get(self, request):
        """ 退出登录 """
        # 清楚用户的session信息
        logout(request)

        # 跳转到首页
        return redirect(reverse('goods:index'))


# /user  参数位置不能错 url匹配来调用基于类视图,它本身没有,会到父类里找,两次调用as_view()方法
# LoginRequiredMixin类的返回值 相当于 对他先进行了认证包装
class UserInfoView(LoginRequiredMixin, View):
    """ 用户中心-信息页 """
    def get(self, request):
        """ 显示 """
        # page = user 传入模板变量进行切换页面hover效果激活判断,

        # 如果当前的用户没有登入, 该属性将设置成AnonymousUser类的一个实例, request.user属性表示当前的用户->返回False
        # 如果当前的用户登入, 它将是User类的实例,  request.user属性表示当前的用户->返回True
        # if request. user.is_authenticated(): 在模板文件中判断用户是否登录了
        # 除了render()给模板文件传递的模板变量之外,django框架会自动把request.user()也传递给模板文件.

        # 获取用户的个人信息
        user = request.user
        address = Address.objects.get_default_address(user)
        # 获取用户的历史浏览记录
        # from redis import StrictRedis
        # sr = StrictRedis(host='', port='6379', db=9)
        # 为了避免储存新的原生连接所产生的另一份设置, django-redis 提供了方法
        # 1. 链接到redis数据库
        con = get_redis_connection('default')
        # 拼接出保存历史浏览的key
        history_key = 'history_%d'%user.id
        # 2. 获取用户最新浏览的5个商品的id
        sku_ids = con.lrange(history_key, 0, 4)  # [2,3,1]
        # 3. 从数据库中查询用户浏览的商品信息
        # goods_li = GoodsSKU.objects.filter(id__in=sku_ids)
        # goods_res = []
        # for a_id in sku_ids:
        #     for goods in goods_li:
        #         if a_id == goods.id:
        #             goods_res.append(goods)
        # 遍历获取用户浏览的历史商品信息  要和用户浏览的保持一致
        goods_li = []
        for id in sku_ids:
            goods = GoodsSKU.objects.get(id=id)
            goods_li.append(goods)

        # 组织上下文
        context = {'page': 'user',
                   'address': address,
                   'goods_li': goods_li}

        return render(request, 'user_center_info.html', context)


# /user/order
class UserOrderView(LoginRequiredMixin, View):
    """ 用户中心-订单页 """
    def get(self, request):
        """ 显示 """
        # page = order
        # 获取用户的订单信息

        return render(request, 'user_center_order.html', {'page': 'order'})


# /user/address
class AddressView(LoginRequiredMixin, View):
    """ 用户中心-地址页 """
    def get(self, request):
        """ 显示 """
        # page = address

        # 获取登录用户对应User对象
        user = request.user

        # 获取用户的默认收货地址
        # try:
        #     address = Address.objects.get(user=user, is_default=True)  # models.Manager
        # except Address.DoesNotExist:
        #     # 不存在默认收货地址
        #     address = None
        address = Address.objects.get_default_address(user)

        return render(request, 'user_center_site.html', {'page': 'address', 'address': address})

    def post(self, request):
        """ 地址的添加 """
        # 接收数据
        receiver = request.POST.get('receiver')
        addr = request.POST.get('addr')
        zip_code = request.POST.get('zip_code')
        phone = request.POST.get('phone')

        # 校验数据  zip_code 因为编码设置可以为null, 可不校验
        if not all([receiver, addr, phone]):
            return render(request, 'user_center_site.html', {'errmsg': '数据不完整'})

        # 校验手机号
        if not re.match(r'^1[3|4|5|7|8][0-9]{9}$', phone):
            return render(request, 'user_center_site.html', {'errmsg': '手机格式不正确'})

        # 业务处理：地址添加
        # 如果用户已存在默认收货地址，添加的地址不作为默认收货地址，否则作为默认收货地址
        # 获取登录用户对应User对象
        user = request.user

        # try:
        #     address = Address.objects.get(user=user, is_default=True)
        # except Address.DoesNotExist:
        #     # 不存在默认收货地址
        #     address = None
        address = Address.objects.get_default_address(user)

        # 存在,则添加的不设为默认地址
        if address:
            is_default = False
        else:
            is_default = True

        # 添加地址 向Address表里添加信息
        Address.objects.create(user=user,
                               receiver=receiver,
                               addr=addr,
                               zip_code=zip_code,
                               phone=phone,
                               is_default=is_default)

        # 返回应答,刷新地址页面
        return redirect(reverse('user:address'))  # get请求方式
















