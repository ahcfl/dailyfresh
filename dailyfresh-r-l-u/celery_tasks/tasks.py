# 使用celery
import time
from celery import Celery
from django.conf import settings
from django.core.mail import send_mail

# 在任务处理者一端加这几句加载配置文件初始化
# import os
# import django
# os.environ.setdefault("DJANGO_SETTINGS_MODULE", "dailyfresh.settings")
# django.setup()

# 创建一个Celery类的实例对象  第一个参数是启动之后app对应的名字可随意指定(一般默认是任务路径) ,
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
    html_message = '<h1>%s, 欢迎您成为天天生鲜的注册会员</h1>请点击下面链接激活您的账户<br/><a href="http://127.0.0.1:8000/user/active/%s">http://127.0.0.1:8000/user/active/%s</a>' % (
    username, token, token)
    # smtp服务器
    send_mail(subject, message, sender, receiver, html_message=html_message)
    # 演示即使睡眠5s发送 , 也不延迟加载goods首页, 异步执行
    # time.sleep(5)




