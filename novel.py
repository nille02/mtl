import lxml
import html
import re
import csv
from typing import List


class Novel:

    chapters: List
    name: str

    def __init__(self, name, chapters, wordlist=None):
        self.name = name
        self.chapters = chapters
        self.wordlist = wordlist


class Chapter:

    chapterid: int
    name: str
    novelname: str
    data: str
    savename: str

    def __init__(self, chapterid, novelname, name, data, savename, wordlist=None):
        self.chapterid = chapterid
        self.name = name
        self.novelname = novelname
        self.data = data
        self.savename = savename
        self.mtl_data = None
        self.word_list = wordlist

    @property
    def size(self) -> int:
        return len(self.data.encode('utf-8'))

    def get_filtered_data(self) -> str:

        data = self.data
        if self.word_list is not None:
            self.word_list = self.__sort(self.word_list, reverse=True)
            for word in self.word_list:
                if len(word) >= 2:
                    data = data.replace(word[0], '[['+word[1]+']]')  # We add [[ and ]] before and after each keyword, later we replace them or delete them.
                else:
                    print("Format Error:" + str(word))

            data = data.replace(']][[', ' ')  # If we have 2 Keywords to close together, we add a space
            data = data.replace(']]', '').replace('[[', '')

        data = data.replace('<!--novel_bn-->\n', '')

        html = lxml.html.fromstring(data)

        for element in html.xpath("//div[contains(@class,'novel_bn')] | //div[contains(@id,'novel_p')][contains(@class,"
                                  "'novel_view')] | //div[contains(@id,'novel_a')][contains(@class,'novel_view')]"):
            parent = element.getparent()
            parent.remove(element)

        for element in html.xpath("//p[contains(@class,'novel_subtitle')]"):
            element.tag = "h2"
            element.attrib['style'] = "text-align: center;"

        html.get_element_by_id("novel_color").set("id", self.chapterid)

        return lxml.html.tostring(html, encoding='unicode')

    # Python code to sort the tuples using first element
    # of sublist Function to sort using sorted()
    def __sort(self, sub_li, reverse=False):

        # reverse = None (Sorts in Ascending order)
        # key is set to sort using first element of
        # sublist lambda has been used
        return (sorted(sub_li, key=lambda x: len(x[0]), reverse=reverse))
