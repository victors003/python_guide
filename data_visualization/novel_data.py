#!/usr/bin/python
# coding=utf8
import os
from os import path as osp
import urllib2
import logging

from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException

__author__ = 'Jam'
__date__ = '2018/12/25 16:02'


class Enum(tuple):
    __getattr__ = tuple.index


BrowserType = Enum(['FIREFOX', 'CHROME', 'IE', 'SAFARI', 'PHANTOMJS'])


class CartoonCat:
    def __init__(self, site, begin=0, end=-1, save_folder="download", browser=BrowserType.FIREFOX, driver=None):
        """
        :param site: 漫画的首页面
        :param begin: 章节的开始(含),0表示第一章
        :param end: 章节的结束(含),-1表示到结尾
        :param browser: 浏览器类型
        :param driver: 驱动，如果驱动程序在可访问的位置，这个参数非必须，对于PhantomJs，驱动程序就是改程序的地址
        """

        self.__site = site
        self.__begin = begin
        self.__end = end
        self.__save_folder = save_folder
        self.__chapter_list = []

        if not osp.exists(self.__save_folder):
            os.mkdir(self.__save_folder)

        if BrowserType.FIREFOX == browser:
            self.__browser = webdriver.Firefox()
        elif BrowserType.CHROME == browser:
            self.__browser = webdriver.Chrome(driver)
        elif BrowserType.IE == browser:
            self.__browser = webdriver.Ie(driver)
        elif BrowserType.SAFARI == browser:
            self.__browser = webdriver.Safari(driver)
        elif BrowserType.PHANTOMJS == browser:
            self.__browser = webdriver.PhantomJS(driver)
        else:
            raise TypeError('UNKNOWN BROWSER TYPE: %s' % browser)

        self.__get_chapter_list()

        if self.__begin >= len(self.__chapter_list) \
                or (0 <= self.__end < self.__begin):
            raise Exception('the begin and end index of chapter is illegal')

        logging.basicConfig(format='[%(asctime)s] %(levelname)s::%(module)s::%(funcName)s() %(message)s', level=logging.INFO)

    def __del__(self):
        self.__browser.quit()

    def __get_chapter_list(self):
        self.__browser.get(self.__site)
        chapter_elem_list = self.__browser.find_elements_by_css_selector('#play_0 ul li a')
        chapter_elem_list.reverse()  # 原本的章节是倒叙的

        for chapter_elem in chapter_elem_list:
            self.__chapter_list.append((chapter_elem.text, chapter_elem.get_attribute('href')))

    @staticmethod
    def __download(url, save_path, try_time=3, timeout=30):
        while try_time > 0:
            try:
                content = urllib2.urlopen(url, timeout=timeout).read()
                with open(save_path, 'wb') as fp:
                    fp.write(content)
                break
            except Exception, et:
                logging.error(et, exc_info=True)
                try_time -= 1
                if try_time == 0:
                    logging.error('cannot download: %s to %s' % (url, save_path))

    def download_chapter(self, chapter_idx, save_folder=None):
        chapter = self.__chapter_list[chapter_idx]

        save_folder = save_folder if save_folder is not None else self.__save_folder

        chapter_title = chapter[0]
        chapter_url = chapter[1]

        logging.info('#### START DOWNLOAD CHAPTER %d %s ####' % (chapter_idx, chapter_title))

        save_folder = osp.join(save_folder, chapter_title)
        if not osp.exists(save_folder):
            os.mkdir(save_folder)

        image_idx = 1

        self.__browser.get(chapter_url)

        while True:
            image_url = self.__browser.find_element_by_css_selector('#qTcms_pic').get_attribute('src')
            save_image_name = osp.join(save_folder, ('%05d' % image_idx) + '.' + osp.basename(image_url).split('.')[-1])
            self.__download(image_url, save_image_name)

            # 通过模拟点击加载下一页，如果已经是最后一页，会有弹窗提示，通过这个确定章节是否下完
            self.__browser.find_element_by_css_selector('a.next').click()
            try:
                self.__browser.find_element_by_css_selector('#bgDiv')
                break
            except NoSuchElementException:
                # 没有结束弹窗，继续下载
                image_idx += 1

        logging.info('#### DOWNLOAD CHAPTER COMPLETE ####')

    def get_chapter_list(self):

        return self.__chapter_list

    def start(self):
        begin = self.__begin if self.__begin >= 0 else 0
        end = self.__end if self.__end >= 0 else len(self.__chapter_list)

        for chapter_idx in xrange(begin, end):
            self.download_chapter(chapter_idx)


if __name__ == '__main__':
    site = 'http://www.tazhe.com/mh/9170/'

    crawler = CartoonCat(
        site=site,                          # 漫画首页
        begin=0,                            # 起始章节
        end=-1,                             # 结束章节
        save_folder='/path/to/download',    # 保存路径，不存在会自动创建
        browser=BrowserType.PHANTOMJS,      # 浏览器类型：FIREFOX，CHROME，SAFARI，IE，PHANTOMJS
        driver='path/to/phantomjs'          # 驱动程序路径，firefox不需要
    )
    crawler.start()
