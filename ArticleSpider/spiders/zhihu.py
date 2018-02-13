# -*- coding: utf-8 -*-
import re
import datetime
import json

try:
    import urlparse as parse
except:
    from urllib import parse

import scrapy
from scrapy.loader import ItemLoader
from ArticleSpider.items import ZhihuAnserItem, ZhihuQuestionItem


class ZhihuSpider(scrapy.Spider):
    name = "zhihu"
    allowed_domains = ["www.zhihu.com"]
    start_urls = ['https://www.zhihu.com/']

    start_answer_url = "https://www.zhihu.com/api/v4/questions/{0}/answers?include=data%5B*%5D.is_normal%2Cis_collapsed%2Ccollapse_reason%2Cis_sticky%2Ccollapsed_by%2Csuggest_edit%2Ccomment_count%2Ccan_comment%2Ccontent%2Ceditable_content%2Cvoteup_count%2Creshipment_settings%2Ccomment_permission%2Cmark_infos%2Ccreated_time%2Cupdated_time%2Crelationship.is_authorized%2Cis_author%2Cvoting%2Cis_thanked%2Cis_nothelp%2Cupvoted_followees%3Bdata%5B*%5D.author.follower_count%2Cbadge%5B%3F(type%3Dbest_answerer)%5D.topics&limit={1}&offset={2}"

    headers = {
        "HOST": "www.zhihu.com",
        "Referer": "https://www.zhihu.com",
        "User-Agent": "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/44.0.2403.89 Safari/537.36"
    }

    '''重写spider的setting中Cookies的默认配置'''
    custom_settings = {
        "COOKIES_ENABLED": True
    }


    def parse(self, response):
        '''
        取出页面所有url，然后遍历每个url,若url带有question/xxx/的发出请求，然后再调用answer请求获取页面
        没有带有question/xxx的url则跳过，继续遍历下一个url。深度优先算法
        '''
        # 取出所有a标签href属性值
        all_urls = response.css("a::attr(href)").extract()
        # 把相对url变为绝对url
        all_urls = [parse.urljoin(response.url, url) for url in all_urls]
        # if/else 配合 fileter 和 lambda这个两个python全局函数 大大简化代码量
        all_urls = filter(lambda x: True if x.startswith('https') else False, all_urls)
        for url in all_urls:
            match_obj = re.match("(.*zhihu.com/question/(\d+))($|/).*", url)
            if match_obj:
                request_url = match_obj.group(1)
                yield scrapy.Request(request_url, headers=self.headers, callback=self.parse_question)
            else:
                pass
            #     if '/logout' not in url:
            #         yield scrapy.Request(url, headers=self.headers, callback=self.parse)


    def parse_question(self, response):
        item_loader = ItemLoader(item=ZhihuQuestionItem(), response=response)
        if "QuestionHeader-title" in response.text:
            match_obj = re.match("(.*zhihu.com/question/(\d+))(/|$).*", response.url)
            if match_obj:
                question_id = match_obj.group(2)

        item_loader.add_value("zhihu_id", question_id)
        item_loader.add_css("topics", ".Tag-content .Popover div::text")
        item_loader.add_css("title", "h1.QuestionHeader-title::text")
        item_loader.add_value("url", response.url)
        item_loader.add_css("content", ".QuestionHeader-detail")
        item_loader.add_css("answer_num", ".List-headerText span::text")
        #item_loader.add_css("comments_num", ".QuestionHeader-actions button::text")
        item_loader.add_css("watch_user_num", ".NumberBoard-value::text")

        question_item = item_loader.load_item()
        yield question_item
        yield scrapy.Request(self.start_answer_url.format(question_id, 20, 0), headers=self.headers, callback=self.parse_answer)


    def parse_answer(self, response):
        ans_json = json.loads(response.text)
        is_end = ans_json["paging"]["is_end"]
        next_url = ans_json["paging"]["next"]

        for answer in ans_json["data"]:
            answer_item = ZhihuAnserItem()
            answer_item["zhihu_id"] = answer["id"]
            answer_item["url"] = answer["url"]
            answer_item["question_id"] = answer["question"]["id"]
            answer_item["author_id"] = answer["author"]["id"] if "id" in answer["author"] else None
            answer_item["content"] = answer["content"] if "content" in answer else None
            answer_item["parise_num"] = answer["voteup_count"]
            answer_item["comments_num"] = answer["comment_count"]
            answer_item["create_time"] = answer["created_time"]
            answer_item["update_time"] = answer["updated_time"]
            answer_item["crawl_time"] = datetime.datetime.now()

            yield answer_item

        if not is_end:
            yield scrapy.Request(next_url, headers=self.headers, callback=self.parse_answer)


    def start_requests(self):

        return [scrapy.Request("https://www.zhihu.com/#signin", callback=self.login, headers=self.headers)]

    def login(self, response):
        response_text = response.text
        match_obj = re.match('.*name="_xsrf" value="(.*?)"', response_text, re.DOTALL)
        xsrf = ""
        if match_obj:
            xsrf=(match_obj.group(1))

        if xsrf:
            post_url = "https://www.zhihu.com/login/phone_num"
            post_data = {
                "_xsrf": xsrf,
                "phone_num": "15361800849",
                "password": "lkj15529",
                "captcha": "",

            }

            import time
            t = str(int(time.time()*1000))
            captcha_url = "https://www.zhihu.com/captcha.gif?r={0}&type=login".format(t)
            yield scrapy.Request(captcha_url, headers=self.headers, meta={"post_data": post_data}, callback=self.login_after_captcha)

            #yield scrapy.Request(post_url, headers=self.headers, meta={"post_data": post_data}, callback=self.check_login)


# 下面这个response就是上面请求返回的图片
    def login_after_captcha(self, response):
        with open("captcha.jpg", "wb") as f:
            f.write(response.body)
            f.close()

        from PIL import Image  # 作用是下载图片
        try:
            im = Image.open("captcha.jpg")
            im.show()
            im.close()
        except:
            pass

        captcha = input("请输入验证码\n>>")

        post_url = "https://www.zhihu.com/login/phone_num"
        post_data = response.meta.get('post_data', {})
        post_data["captcha"] = captcha
        return [scrapy.FormRequest(
            url=post_url,
            formdata=post_data,
            headers=self.headers,
            callback=self.check_login,
        )]


    def check_login(self, response):  # scrapy.Request不写callback回调函数的话，scrapy会自动回调parse函数
        text_json = json.loads(response.text)   #注意是loads（）
        if "msg" in text_json and text_json["msg"] == "登录成功":
            for url in self.start_urls:
                yield scrapy.Request(url, dont_filter=True, headers=self.headers)
