#!/usr/bin/python
#-*- coding: UTF-8 -*-

import re
import logging
import requests
from bs4 import BeautifulSoup
from collections import OrderedDict

from exception import *


CLASS_DISAMBIGUATION = ['nslog:519']
CLASS_CREATOR        = ['nslog:1022']
CLASS_REFERENCE      = ['nslog:1968']
CLASS_TAG            = ['nslog:7336', 'taglist']
CLASS_CONTENT        = {
        'lemmaTitleH1': '===== %(text)s ====\n\n',
        'headline-1': '\n== %(text)s ==\n',
        'headline-2': '\n* %(text)s *\n',
        'para': '%(text)s',
        }

CLASS_SUMMARY = [ 'lemma-summary' ]
CLASS_INFO = ['basicInfo-item']
CLASS_SUMMARY_PIC = ['summary-pic']

CHROME_HEADERS = {
        'Accept-Language': 'zh-CN,zh;q=0.8,zh-TW;q=0.6',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/66.0.3359.139 Safari/537.36',
        }


class Page(object):
    def __init__(self, string, encoding='utf-8'):
        url = 'https://baike.baidu.com/search/word'
        payload = None

        # An url or a word to be Paged
        pattern = re.compile('^https?:\/\/baike\.baidu\.com\/.*', re.IGNORECASE)
        if re.match(pattern, string):
            url = string
        else:
            payload = {'pic':1, 'enc':encoding, 'word':string}

        self.http = requests.get(url, headers=CHROME_HEADERS, params=payload)
        self.html = self.http.content
        self.soup = BeautifulSoup(self.html, "lxml")

        # Exceptions
        if self.soup.find(class_=CLASS_DISAMBIGUATION):
            raise DisambiguationError(string.decode('utf-8'), self.get_inurls())
        if '百度百科尚未收录词条' in self.html:
            raise PageError(string)
        if self.soup.find(id='vf'):
            raise VerifyError(string)

    def parse_basic_info(self):
        """Get basic info of a page"""
        divs = self.soup.find_all(class_=CLASS_INFO)
        info = {}
        name = ""
        for div in divs:
            if 'name' in div.get('class'):
                name = div.get_text(strip=True).replace(u"\xa0", "")
            if 'value' in div.get('class'):
                value = div.get_text(strip=True)
                if not name:
                    logging.error("analyse error, no name for value[%s]" % value)
                    continue
                info[name] = value
                name = None
        return info

    def get_info(self):
        """ Get informations of the page """

        info = self.parse_basic_info()
        title = self.soup.title.get_text()
        info['title'] = title[:title.rfind('_')]
        info['url'] = self.http.url

        try:
            info['page_view'] = self.group.find(id='viewPV').get_text()
            info['last_modify_time'] = self.soup.find(id='lastModifyTime').get_text()
            info['creator'] = self.soup.find(class_=CLASS_CREATOR).get_text()

        finally:
            return info

    def get_content(self):
        """ Get main content of a page """
        content_list = self.soup.find_all(class_=CLASS_CONTENT.keys())
        content = []

        for div in content_list:
            klass = div.get('class')
            text = div.get_text()
            for k,fmt in CLASS_CONTENT.items():
                if k in klass:
                    content.append( fmt % vars() )

        return '\n'.join(content)

    def get_image(self):
        divs = self.soup.find_all(class_=CLASS_SUMMARY_PIC)
        for div in divs:
            img = div.find("img")
            url = img.attrs['src']
            if url: return url
        return ""

    def get_summary(self):
        """Get summary infomation of a page"""
        divs = self.soup.find_all(class_=CLASS_SUMMARY)
        summary = ""
        return '\n'.join( div.get_text(strip=True) for div in divs )

    def get_inurls(self):
        """ Get links inside a page """
        inurls = OrderedDict()
        href = self.soup.find_all(href=re.compile('\/(sub)?view(\/[0-9]*)+.htm'))

        for url in href:
            inurls[url.get_text()] = 'https://baike.baidu.com%s'%url.get('href')

        return inurls


    def get_tags(self):
        """ Get tags of the page """
        tags = []
        for tag in self.soup.find_all(class_=CLASS_TAG):
            tags.append(tag.get_text(strip=True))

        return tags

    def get_references(self):
        """ Get references of the page """

        references = []
        for ref in self.soup.find_all(class_=CLASS_REFERENCE):
            r = {}
            r['title'] = ref.get_text()
            r['url'] = ref.get('href')
            references.append(r)

        return references



class Search(object):
    def __init__(self, word, results_n=10, page_n=1):
        # Generate searching URL
        url = 'https://baike.baidu.com/search'
        pn = (page_n - 1) * results_n
        payload = {'type':0, 'submit':'search', 'pn':pn, 'rn':results_n, 'word':word}

        self.http = requests.get(url, headers=CHROME_HEADERS, params=payload)
        self.html = self.http.content
        self.soup = BeautifulSoup(self.html)


    def get_results(self):
        """ Get searching results """

        search_results = []
        items = self.soup.find_all(class_='f')      # get results items

        for item in items:
            result = {}
            a = item.find('a')
            title = a.get_text()                    # get result title
            title = title[:title.rfind('_')]
            result['title'] = title
            result['url'] = a.get('href')           # get result links
            # get result discription
            result['discription'] = item.find(class_='abstract').get_text().strip()
            search_results.append(result)

        return search_results

