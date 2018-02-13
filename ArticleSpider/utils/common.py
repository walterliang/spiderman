# -*-  coding: utf-8 -*-
import hashlib
import re


def get_md5(url):
    if isinstance(url, str):  # 若url是unicode类型,这里str在python默认就是unicode编码类型
        url = url.encode("utf-8")
    m = hashlib.md5()
    m.update(url)
    return m.hexdigest()


def extract_num(text):
    # 从字符串中提取数字
    match_obj = re.match(".*?(\d+).*", text)
    if match_obj:
        nums = int(match_obj.group(1))
    else:
        nums = 0
    return nums


if __name__ == "__main__":
    print (get_md5("https://www.jobbole.com".encode('utf-8')))
# python3默认字符串是unicode的，而hashlib中参数不支持unicode,所以要使用encode()转为utf-8