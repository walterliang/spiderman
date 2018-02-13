# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html
import codecs
import json

import MySQLdb
import MySQLdb.cursors

from scrapy.pipelines.images import ImagesPipeline  # 不仅能保存图片，还能对图片进行转换、过滤

# scrapy本身有很多可以导出item的工具,如下
from scrapy.exporters import JsonItemExporter
from twisted.enterprise import adbapi   # adbapi可以把mysql的操作变成异步的操作


class ArticlespiderPipeline(object):
    def process_item(self, item, spider):
        return item


# 自定义pipeline保存item到json文件中
class JsonWithEncodingPipeline(object):
    def __init__(self):
        self.file = codecs.open("article.json", "w", encoding="utf-8")

    def process_item(self, item, spider):
        lines = json.dumps(dict(item), ensure_ascii=False) + "\n"
        # ensure_ascii=False确保写入中文不会报错
        self.file.write(lines)
        return item
    # 关闭文件
    def spider_closed(self, spider):
        self.file.close()


# 使用scrapy提供的json exporter来导出item
class JsonExporterPipleline(object):
    def __init__(self):
        self.file = open('articleexport.json', 'wb')
        self.exporter = JsonItemExporter(self.file, encoding='utf-8', ensure_ascii=False)
        self.exporter.start_exporting()

    def close_spider(self, spider):
        self.exporter.finish_exporting()
        self.file.close()

    def process_item(self, item, spider):
        self.exporter.export_item(item)
        return item


# 这个Pipeline是把item用同步的方式写入mysql

class MysqlPipeline(object):
    # 采用同步的机制写入mysql
    def __init__(self):
        self.conn = MySQLdb.connect('127.0.0.1', 'root', 'root', 'article_spider', charset="utf8", use_unicode=True)
        self.cursor = self.conn.cursor()

    def process_item(self, item, spider):
        insert_sql = """
            insert into article_detail(title, url, create_date, fav_nums)
            VALUES (%s, %s, %s, %s)
        """
        self.cursor.execute(insert_sql, (item["title"], item["url"], item["create_date"], item["fav_nums"]))
        self.conn.commit()


# 用异步的方式写入数据库  ,关于写入数据库，还可以用scrapy-djangoitem库，使用ORM方式写入数据库,github上有
class MysqlTwistedPipeline(object):
    def __init__(self, dbpool):
        self.dbpool = dbpool  # 下面类方法传过来的dbpool

    @classmethod
    def from_settings(cls, settings):
        dbparms = dict(
            host=settings["MYSQL_HOST"],
            db=settings["MYSQL_DBNAME"],
            user=settings["MYSQL_USER"],
            passwd=settings["MYSQL_PASSWORD"],
            charset='utf8',
            cursorclass=MySQLdb.cursors.DictCursor,
            use_unicode=True,
        )
        dbpool = adbapi.ConnectionPool("MySQLdb", **dbparms)

        return cls(dbpool)  # 这里返回类的实例

    def process_item(self, item, spider):
        # 使用twisted.adbapi将mysql插入变成异步执行
        query = self.dbpool.runInteraction(self.do_insert, item)
        query.addErrback(self.handle_error, item, spider)  # 处理异常

    def handle_error(self, failure, item, spider):
        # 处理异步插入的异常
        print(failure)


    # 会从dbpool拿出一个cursor放到下面，作为第二个参数
    def do_insert(self, cursor, item):
        insert_sql, params = item.get_insert_sql()
        cursor.execute(insert_sql, params)

        # 执行具体的插入
        # insert_sql = """
        #             insert into article_detail(title, url, create_date, fav_nums)VALUES (%s, %s, %s, %s)
        #         """
        # cursor.execute(insert_sql, (item["title"], item["url"], item["create_date"], item["fav_nums"]))




# 自定义一个Pipeline,目的是【获取下载图片的路径】---从ImagesPipeline中重载这个方法,可看到路径放在参数results中
# 同时若在setting中配置这个pipeline，也能下载图片，因为它继承了ImagesPipeline
class ArticleImagePipeline(ImagesPipeline):
    def item_completed(self, results, item, info):  # 通过调试，得知results是个[（成功/失败,{'path':'文件保存路径'}），（），..]
        if "front_image_path" in item:
            for ok, value in results:
                image_file_path = value['path']
            item['front_image_path'] = image_file_path
        return item  # 记得传回去item,看setting中每个pipeline的顺序，就是item的传送顺序







