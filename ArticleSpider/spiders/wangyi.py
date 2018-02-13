# -*- coding: utf-8 -*-
import scrapy
from ArticleSpider.items import A163Item, A163ItemLoader

from selenium import webdriver
from scrapy.xlib.pydispatch import dispatcher
from scrapy import signals


class WangyiSpider(scrapy.Spider):
    name = "wangyi"
    allowed_domains = ["money.163.com"]
    start_urls = ['http://money.163.com/']

    def __init__(self):
        self.browser = webdriver.Chrome(executable_path="G:/dj/chromedriver.exe")
        super(WangyiSpider, self).__init__()
        dispatcher.connect(self.spider_close, signals.spider_closed)

    def spider_close(self, spider):
        print("spider close")
        self.browser.close()

    def parse(self, response):
        comments_urls = response.css(".tie_count::attr(href)").extract()
        for node_url in comments_urls:
            yield scrapy.Request(url=node_url, callback=self.parse_item)

    def parse_item(self, response):

        item_load = A163ItemLoader(item=A163Item(), response=response)

        item_load.add_css("title", ".wrapper.origPost h1 a::text")

        item_load.add_css("comments_nums", ".titleBar.titleBar-blue .text span em::text")

        item_load.add_css("comment_body", ".page-block .body p::text")

        comments_item = item_load.load_item()

        return comments_item


