# _*_ coding:utf-8 _*_
__author__ = 'bobby'
__date__ = '2017-04-23 21:53'
import sys
import os

from scrapy.cmdline import execute

#说明这个scrapy工程目录
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
#传入命令
#execute(["scrapy", "crawl", "jobbole"])
#execute(["scrapy", "crawl", "zhihu"])
#execute(["scrapy", "crawl", "lagou"])
execute(["scrapy", "crawl", "wangyi"])




