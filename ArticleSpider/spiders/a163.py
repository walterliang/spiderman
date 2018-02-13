# -*- coding: utf-8 -*-
import scrapy
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule
from ArticleSpider.items import A163Item, A163ItemLoader

from selenium import webdriver
from scrapy.xlib.pydispatch import dispatcher
from scrapy import signals

#
# class A163Spider(CrawlSpider):
#     name = 'a163'
#     allowed_domains = ['money.163.com']
#     #start_urls = ['http://news.163.com/']
#     start_urls = ['http://money.163.com/']
#
#     rules = (
#         Rule(LinkExtractor(allow=('17/\d+.html',)), follow=True),
#         Rule(LinkExtractor(allow=r'comment.\.*.html/'), callback='parse_item', follow=True),
#     )




