# dailyfresh
dailyfresh mall based on B2C model
基于B2C的天天生鲜商城

  B2C(Business-to-Customer), 企业对个人的一种商业模式，简称"商对客"。 
  商对客是电子商务的一种模式，这种电子商务一般以网络零售业为主，主要借助于互联网开展在线销售活动。
  B2C即企业通过互联网为消费者提供一个新型的购物环境——网上商店，消费者通过网络在网上购物、网上支付等消费行为。

## 从0开始，立项、构建、开发到部署

遇到bug可参考笔记总结：

https://github.com/ahcfl/puzzle.git

https://github.com/ahcfl/dailyfresh/tree/main/notes

CSDN博客：

https://blog.csdn.net/mmmmmCJP?spm=1011.2124.3001.5113

一、技术栈

    1. 语言：Python3.* (Django)
    2. 数据库: MySql、 redis
    3. 任务队列(异步处理): celery(django-celery)
    4. 分布式文件存储: FastDFS
    5. 搜索引擎(商品检索)： haystack(django-haystack)、whoosh、二次开发
    6. web服务器配置: Nginx+ uwsgi
    7. 开发环境： PyCharm、Linux、vim

二、技术架构

    1. 开发架构
       采用BS结构, 即Browser/Server(浏览器/服务器)结构,构建一个web的网站商城系统, 
       其架构逻辑:frame

    2. 部署架构
       Nginx+uwsgi
       deploy

三、主体模块

    1. 用户模块
    2. 商品相关模块
    3. 购物车相关模块
    4. 订单相关模块  

四、数据库表设计
    
    注意SPU和SKU的思想概念：
    1. SPU是商品信息聚合的最小单位，是一组可复用、易检索的标准化信息的集合，该集合描述了一个产品的特性。
       通俗点讲，属性值、特性相同的商品就可以称为一个SPU。
       例如，iphone7就是一个SPU，N97也是一个SPU，这个与商家无关，与颜色、款式、套餐也无关。
    2. SKU即库存进出计量的单位， 可以是以件、盒、托盘等为单位，在服装、鞋类商品中使用最多最普遍。
       例如，纺织品中一个SKU通常表示：规格、颜色、款式。

五、功能与性能优化

    案例1：用户注册发激活邮件时，可能发送邮件所需的时间较长，客户端会需要等待，用户体验不好。
    案例2：用户访问量过大时，每次都需要从数据库动态获取首页页面数据，数据库查询次数较多，也要考虑到DDOS攻击。

    改进: 把耗时的任务放到后台异步执行，此处使用celery任务队列, 其中使用redis作中间件。

    1. redis存储用户历史浏览记录, 采用list数据结构: 
       History_用户id: [skuid1,skuid2,skuid3]
    
    2. 使用redis存储用户购物车商品信息，采用hash数据结构:
       cart_userid: {'sku_id1': num, 'sku_id2': num}
    
    3. 采用分布式文件系统,把商品图片等信息存储在FastDFS系统中,
       Nginx+FastDFS配合, 减少服务器的压力
    
    4. 页面静态化： 首页、商品列表页、商品详情页等用户共同的页面,
       把页面静态化，以减少对数据库的操作。当后台数据更改时自动重新生成静态页面。
       
    5. 页面数据缓存，把页面使用的数据存放在缓存中，当再次使用这些数据时，
       先从缓存中获取，如获取不到，再去查询数据库，减少数据库的查询次数
       
    6. 订单并发
