import requests
import os
import re
import random
import logging
from lxml import etree
from urllib.parse import urljoin


class RandomHeaders(object):
    ua_list = [
        'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/535.1 (KHTML, like Gecko) Chrome/14.0.835.163 Safari/535.1',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/73.0.3683.103 Safari/537.36Chrome 17.0',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_7_0) AppleWebKit/535.11 (KHTML, like Gecko) Chrome/17.0.963.56 Safari/535.11',
        'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:6.0) Gecko/20100101 Firefox/6.0Firefox 4.0.1',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.6; rv:2.0.1) Gecko/20100101 Firefox/4.0.1',
        'Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10_6_8; en-us) AppleWebKit/534.50 (KHTML, like Gecko) Version/5.1 Safari/534.50',
        'Mozilla/5.0 (Windows; U; Windows NT 6.1; en-us) AppleWebKit/534.50 (KHTML, like Gecko) Version/5.1 Safari/534.50',
        'Opera/9.80 (Windows NT 6.1; U; en) Presto/2.8.131 Version/11.11',
    ]
    @property
    def random_headers(self):
        return {
            'User-Agent': random.choice(self.ua_list)
        }


class UrlHandler(RandomHeaders):
    def __init__(self, url):
        self.url = url

    def parse_home_list(self, url):
        response = requests.get(url, headers=self.random_headers, timeout=6).content.decode("gbk")
        req = etree.HTML(response)
        href_list = req.xpath('//dl[@class="imglist"]/dt/ul[@class="listimg"]/li/span[@class="listpic"]/a/@href')
        for href in href_list:
            item = self.parse_detail(href)
            yield item

    def parse_detail(self, url):
        try:
            response = requests.get(url, headers=self.random_headers, timeout=6).content.decode("gbk")
        except Exception as e:
            print(e.args)
            self.parse_detail(url)
        else:
            resp = etree.HTML(response)
            try:
                name_ = resp.xpath('//div[@class="arcinfo"]/h2/text()')[0]
            except IndexError:
                pass
            else:
                name = self.validate_title(name_)
                img_url_list_ = resp.xpath('//div[@class="contentinfo"]/table//@src')
                img_url_list = [urljoin('http://www.uimaker.com', img_url) for img_url in img_url_list_]
                ai_url = ''
                if int(resp.xpath('//div[@class="download"]/dl[@class="downlink"]/dd[1]/b/text()')[0]) == 0:
                    try:
                        ai_url = resp.xpath('//div[@class="download"]/dl[@class="downlink"]/dt/li/a/@href')[0]
                    except IndexError:
                        ai_url = ''
                return name, img_url_list, ai_url

    @staticmethod
    def validate_title(title):
        pattern = r"[\/\\\:\*\?\"\<\>\|]"
        new_title = re.sub(pattern, "_", title)  # 替换为下划线
        return new_title

    def get_tasks(self):
        data_list = self.parse_home_list(self.url)
        for item in data_list:
            yield item


class Download(RandomHeaders):
    def __init__(self, data_list, dl_dir='DownLoad', has_psd=True):
        self.dl_dir = dl_dir
        os.makedirs(self.dl_dir, exist_ok=True)
        self.has_pad = has_psd
        self.data_list = data_list

    def save2ai(self, ai_url, name):
        print("开始下载素材-->", name, ai_url)
        try:
            r = requests.get(ai_url, headers=self.random_headers, timeout=6)
        except Exception as e:
            print(e.args)
            print('下载数据失败-->', name, ai_url, )
        else:
            with open('{}/{}/{}.zip'.format(self.dl_dir, name, name), 'wb') as f:
                f.write(r.content)
            print("素材下载完成-->", name, ai_url,)

    # 下载图片
    def save2img(self, name, url):
        print("\n开始下载图片-->:", url, '\n')
        try:
            r = requests.get(url, headers=self.random_headers, timeout=6)
        except Exception as e:
            print(e.args)
        else:
            img_name = url.split('/')[-1]
            if img_name:
                try:
                    with open(f'{self.dl_dir}/{name}/{img_name}', 'wb') as f:
                        f.write(r.content)
                except PermissionError:
                    logging.critical('--权限错误:--', '\n')
                else:
                    print('图片下载完成-->:', name, url, '\n')
            else:
                print('获取图片名称失败-->:', name, url, '\n')

    def work(self):
        if self.data_list is None:
            return
        try:
            name, img_urls, _ = self.data_list
            file_path = self.dl_dir + '/' + name
            os.makedirs(file_path, exist_ok=True)
        except ValueError or TypeError:
            print('错误数据', self.data_list, '\n')
        else:
            for img_url in img_urls:
                self.save2img(name, img_url)
            if self.has_pad:
                if _:
                    self.save2ai(_, name)


if __name__ == '__main__':
    url = 'http://www.uimaker.com/uimakerdown/list_36_1.html'
    u_handler = UrlHandler(url)
    for data in u_handler.get_tasks():
        print(data)
