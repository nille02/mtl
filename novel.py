import lxml
import html
import re
import csv
from typing import List
from typing import Dict
import novel


class Novel:
    chapters: List
    name: str
    volumes: dict
    wordlist: List

    def __init__(self, name: str, chapters: List, volumes: dict = None, wordlist: List = None):
        if volumes is None:
            volumes = {}
        self.name = name
        self.chapters = chapters
        self.volumes = volumes
        if wordlist is None:
            wordlist = []
        self.wordlist = wordlist

    def get_volumes(self) -> dict:
        return self.volumes


class Chapter:
    chapterid: int
    name: str
    novelname: str
    data: str
    savename: str
    chapter_number: str

    def __init__(self, chapterid: int, novelname: str, name: str, data: str, savename,
                 wordlist=None, chapter_number=""):
        self.chapterid = chapterid
        self.name = name
        self.novelname = novelname
        self.data = data
        self.savename = savename
        self.word_list = wordlist
        self.chapter_number = chapter_number

    @property
    def size(self) -> int:
        return len(self.data.encode('utf-8'))

    def get_filtered_data(self) -> str:

        data = self.data
        if self.word_list is not None:
            for word in self.word_list:
                if len(word) >= 2:
                    # We add [[ and ]] before and after each keyword, later we replace or delete them.
                    data = data.replace(word[0], '[[' + word[1] + ']]')
                else:
                    print("Format Error:" + str(word))

            data = data.replace(']][[', ' ')  # If we have 2 Keywords to close together, we add a space
            data = data.replace(']]', '</span>').replace('[[', '<span lang=\"en\">')

        data = data.replace('<!--novel_bn-->\n', '')

        parsed_html = lxml.html.fromstring(data)

        for element in parsed_html.xpath("//div[contains(@class,'novel_bn')]"
                                         " | //div[contains(@id,'novel_p')][contains(@class,'novel_view')]"
                                         " | //div[contains(@id,'novel_a')][contains(@class,'novel_view')]"):
            parent = element.getparent()
            parent.remove(element)

        for element in parsed_html.xpath("//p[contains(@class,'novel_subtitle')]"):
            element.tag = "h2"
            element.attrib['style'] = "text-align: center;"

        parsed_html.get_element_by_id("novel_color").set("id", str(self.chapterid))

        return self.__remove_ruby_tags(lxml.html.tostring(parsed_html, encoding='unicode'))

    @staticmethod
    def __remove_ruby_tags(data: str) -> str:
        # The First Pattern Replace all Ruby blocks with ・ as the only character in it
        MATCH_PATTERN = r"<ruby><rb>(?P<first>.+?)</rb><rp>.+?</rp><rt>(?P<second>・+?)</rt><rp>.+?</rp></ruby>"
        data = re.sub(MATCH_PATTERN, r'<span>\g<first></span>', data)
        # This Pattern remove all ruby blocks and move its content after the word in ()
        MATCH_PATTERN = r"<ruby><rb>(?P<first>.+?)</rb><rp>.+?</rp><rt>(?P<second>.+?)</rt><rp>.+?</rp></ruby>"
        data = re.sub(MATCH_PATTERN, r'<span>\g<first>(\g<second>)</span>', data)
        return data
