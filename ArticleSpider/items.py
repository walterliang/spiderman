# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html
import datetime, re
import scrapy

from scrapy.loader import ItemLoader
from scrapy.loader.processors import MapCompose, TakeFirst, Join
from ArticleSpider.utils.common import extract_num
from ArticleSpider.settings import SQL_DATE_FORMAT, SQL_DATETIME_FORMAT

from w3lib.html import remove_tags


class ArticlespiderItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    pass


def add_something(value):
    return value+'-from_jobbole'


def date_convert(value):
    try:
        create_date = datetime.datetime.strptime(value, "%Y/%m/%d").date()
    except Exception as e:
        create_date = datetime.datetime.now().date()
    return create_date


def remove_comment_tas(value):
    if "评论" in value:
        return ''
    else:
        return value


def get_nums(value):
    match_re = re.match('.*?(\d+).*', value)
    if match_re:
        nums = match_re.group(1)
    else:
        nums = 0
    return nums


def return_value(value):  # 专门为了front_image_ulr设定的，保证写入item时是个list对象，在下载图片时才不会报错
    return value


class ArticleItemLoader(ItemLoader): # 为了解决每次都取第一个值，自定义一个itemloader(不是item对象)
    default_output_processor =TakeFirst()  # 但是这里会把list对象转为str对象。
    # ****下面的output_processor会覆盖这个默认的


class JobBoleArticleItem(scrapy.Item):

    title = scrapy.Field(
        input_processor=MapCompose(add_something) # title的input预先处理器
    )
    front_image_url = scrapy.Field(
        output_processor=MapCompose(return_value)  # 因为若要配置ImagePipele,该字段必须是list
                                                   # 所以要覆盖下默认的output_processor
    )

    front_image_path = scrapy.Field()
    # 重点--如何把response中的图片保存到本地呢
    # 通过在setting中配置ITEM_PIPELINES
    # 如何给这个Item赋值呢（即把图片的路径写入这个item的front_image_path字段）--自定义pipeline

    create_date = scrapy.Field(
        input_processor=MapCompose(date_convert),
        # output_processor=TakeFirst()
    )


    url = scrapy.Field()  # 当前文章详情页的url

    url_object_id = scrapy.Field()  # 如何通过加密把url转为固定长度的str?作为id用作标识？

    comment_nums = scrapy.Field(
        input_processor=MapCompose(get_nums)
    )
    fav_nums = scrapy.Field(
        input_processor=MapCompose(get_nums)
    )
    praise_nums = scrapy.Field(
        input_processor=MapCompose(get_nums)
    )

    tags = scrapy.Field(
        input_processor=MapCompose(remove_comment_tas),
        output_processor=Join(',')
    )

    content = scrapy.Field()
# 11个字段


class ZhihuQuestionItem(scrapy.Item):
    # 问题的item---10
    zhihu_id = scrapy.Field()
    topics = scrapy.Field()
    url = scrapy.Field()
    title = scrapy.Field()
    content = scrapy.Field()
    answer_num = scrapy.Field()
    #comments_num = scrapy.Field()
    watch_user_num = scrapy.Field()
    click_num = scrapy.Field()
    crawl_time = scrapy.Field()

    def get_insert_sql(self):
        # 插入知乎问题表的sql语句,下面的on duplicate key update 是为了重复插入时，更新对应字段值
        insert_sql = """
              insert into zhihu_question(zhihu_id, topics, url, title, content,
                  answer_num, watch_user_num, click_num, crawl_time)
              VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
               ON DUPLICATE KEY UPDATE content=VALUES(content), answer_num=VALUES(answer_num),
                watch_user_num=VALUES(watch_user_num),
               click_num=VALUES(click_num)
              """

        zhihu_id = self["zhihu_id"][0]
        topics = ",".join(self["topics"])
        url = self["url"][0]
        title = "".join(self["title"])
        content = "".join(self["content"])
        answer_num = extract_num("".join(self["answer_num"]))
        #comments_num = extract_num("".join(self["comments_num"]))

        if len(self["watch_user_num"]) == 2:
            watch_user_num = int(self["watch_user_num"][0])
            click_num = int(self["watch_user_num"][1])
        else:
            watch_user_num = int(self["watch_user_num"][0])
            click_num = 0

        crawl_time = datetime.datetime.now().strftime(SQL_DATETIME_FORMAT)

        params = (zhihu_id, topics, url, title, content, answer_num, watch_user_num,
                  click_num, crawl_time)

        return insert_sql, params



class ZhihuAnserItem(scrapy.Item):
    zhihu_id = scrapy.Field()
    url = scrapy.Field()
    question_id = scrapy.Field()
    author_id = scrapy.Field()
    content = scrapy.Field()
    parise_num = scrapy.Field()
    comments_num = scrapy.Field()
    create_time = scrapy.Field()
    update_time = scrapy.Field()
    crawl_time = scrapy.Field()


    def get_insert_sql(self):
        # 插入知乎answer表的sql语句,[on duplicate key update] 是为了重复插入时，更新对应字段值
        insert_sql = '''
                insert into zhihu_answer(zhihu_id, url, question_id, author_id, content, parise_num, comments_num,
                  create_time, update_time, crawl_time)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE content=VALUES(content), comments_num=VALUES(comments_num),parise_num=VALUES(parise_num),
                  update_time=VALUES(update_time)
        '''

        create_time = datetime.datetime.fromtimestamp(self["create_time"]).strftime(SQL_DATETIME_FORMAT)
        update_time = datetime.datetime.fromtimestamp(self["update_time"]).strftime(SQL_DATETIME_FORMAT)
        params = (
            self["zhihu_id"], self["url"], self["question_id"],
            self["author_id"], self["content"], self["parise_num"],
            self["comments_num"], create_time, update_time,
            self["crawl_time"].strftime(SQL_DATETIME_FORMAT),
        )

        return insert_sql, params




def remove_splash(value):
    #去掉工作城市的斜线
    return value.replace("/","")

def handle_jobaddr(value):
    addr_list = value.split("\n")
    addr_list = [item.strip() for item in addr_list if item.strip()!="查看地图"]
    return "".join(addr_list)


class LagouJobItemLoader(ItemLoader): # 为了解决每次都取第一个值，自定义一个itemloader(不是item对象)
    default_output_processor =TakeFirst()  # 但是这里会把list对象转为str对象。


class LagouJobItem(scrapy.Item):
    "拉勾网职位信息"
    title = scrapy.Field()
    url = scrapy.Field()
    url_object_id = scrapy.Field()
    salary = scrapy.Field()

    # input_processor :是处理填入item前的数据格式
    # output_processor则相反
    # MapCompose(func) 处理方法

    job_city = scrapy.Field(
        input_processor=MapCompose(remove_splash),
    )
    work_years = scrapy.Field(
        input_processor = MapCompose(remove_splash),
    )
    degree_need = scrapy.Field(
        input_processor = MapCompose(remove_splash),
    )
    job_type = scrapy.Field()
    publish_time = scrapy.Field()
    job_advantage = scrapy.Field()
    job_desc = scrapy.Field()
    job_addr = scrapy.Field(
        input_processor=MapCompose(remove_tags, handle_jobaddr),
    )
    company_name = scrapy.Field()
    company_url = scrapy.Field()
    tags = scrapy.Field(
        input_processor = Join(",")
    )
    crawl_time = scrapy.Field()

    def get_insert_sql(self):
        insert_sql = """
            insert into lagou_job(title, url, url_object_id, salary, job_city, work_years, degree_need,
            job_type, publish_time, job_advantage, job_desc, job_addr, company_name, company_url,
            tags, crawl_time) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE salary=VALUES(salary), job_desc=VALUES(job_desc)
        """
        params = (
            self["title"], self["url"], self["url_object_id"], self["salary"], self["job_city"],
            self["work_years"], self["degree_need"], self["job_type"],
            self["publish_time"], self["job_advantage"], self["job_desc"],
            self["job_addr"], self["company_name"], self["company_url"],
            self["job_addr"], self["crawl_time"].strftime(SQL_DATETIME_FORMAT),
        )

        return insert_sql, params


class A163ItemLoader(ItemLoader):
    default_output_processor = TakeFirst()  #但是这里会把list对象转为str对象。

class A163Item(scrapy.Item):
    '''
    网易评论
    '''
    title = scrapy.Field()
    comments_nums = scrapy.Field()
    # ding_nums = scrapy.Field()
    # cai_nums = scrapy.Field()
    # remark_time = scrapy.Field()
    comment_body = scrapy.Field()

    def get_insert_sql(self):
        insert_sql = """
            insert into 163_comments(title, comments_nums, comment_body) VALUES (%s,  %s, %s)
        """
        params = (
            self["title"], self["comments_nums"], self["comment_body"]
        )

        return insert_sql, params





