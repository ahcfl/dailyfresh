# 定义索引类
from haystack import indexes
# 导入你的模型类
from goods.models import GoodsSKU


# 指定对于某个类的某些数据建立索引
# 索引类名格式:模型类名+Index
class GoodsSKUIndex(indexes.SearchIndex, indexes.Indexable):
    # 索引字段 use_template=True --> 指定根据表中的哪些字段建立索引文件 --> 它的说明放在一个文件中
    text = indexes.CharField(document=True, use_template=True)

    # 返回你的模型类
    def get_model(self):

        return GoodsSKU

    # 建立索引的数据
    def index_queryset(self, using=None):
        # get_model().objects.all()--> 对这个方法返回的内容建立索引
        return self.get_model().objects.all()

