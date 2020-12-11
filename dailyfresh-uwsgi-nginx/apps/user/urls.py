from django.conf.urls import url
from django.contrib.auth.decorators import login_required
# from user import views
from user.views import RegisterView, ActiveView, LoginView, UserInfoView, UserOrderView, AddressView, LogoutView

# 因为 Django 的 URL 解析器期望发送请求和相关参数来调动函数而不是类，基于(View)类的视图有一个 as_view() 类方法，
# 这个函数创建一个类的实例，调用 setup() 初始化它的属性，然后调用 dispatch() 方法。
# dispatch 观察请求并决定它是 GET 和 POST，等等。

urlpatterns = [

    # url(r'^register$', views.register, name='register'),     # 注册用户账户
    # url(r'^register_handle$', views.register_handle, name='register_handle'),   # 用户注册处理

    url(r'^register$', RegisterView.as_view(), name='register'),            # 注册用户
    url(r'^active/(?P<token>.*)$', ActiveView.as_view(), name='active'),     # 用户激活

    url(r'^login$', LoginView.as_view(), name='login'),                     # 用户登录
    url(r'^logout$', LogoutView.as_view(), name='logout'),                    # 用户退出

    url(r'^$', UserInfoView.as_view(), name='user'),  # 用户中心-信息页
    url(r'^order/(?P<page>\d+)$', UserOrderView.as_view(), name='order'),  # 用户中心-订单页
    url(r'^address$', AddressView.as_view(), name='address'),  # 用户中心-地址页

    # url(r'^$', login_required(UserInfoView.as_view()), name='user'), # 用户中心-信息页
    # url(r'^order$', login_required(UserOrderView.as_view()), name='order'), # 用户中心-订单页
    # url(r'^address$', login_required(AddressView.as_view()), name='address'), # 用户中心-地址页



]

