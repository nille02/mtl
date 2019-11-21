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

    def get_filtered_novel(self):
        if self.wordlist is not None:
            for chapter in self.chapters:
                filtered_data = chapter.get_filtered_data()
                # for word in self.wordlist: # This Block makes no sense.
                #     filtered_data = filtered_data.replace(word[0], word[1])
                chapter.data = filtered_data
        else:
            return self




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

    @property
    def merged_size(self) -> int:
        return len(self.merged_data.encode('utf-8'))

    @property
    def merged_data(self) -> str:
        match = re.compile(r"^<p ((class=\"novel_subtitle\")|id=\"L(\d+)\")>(.+)(<\/p>)")
        match2 = re.compile(r"> (.+) <")

        if self.mtl_data is None:
            return None

        raw_html = lxml.html.fromstring(self.get_filtered_data())
        mtl_html = lxml.html.fromstring(self.mtl_data)

        for raw, mtl in zip(raw_html.xpath("//p"), mtl_html.xpath("//p")):

            if raw.text is None or mtl.text is None:
                continue

            parent = raw.getparent()

            span_ja = '<span lang=\"ja\">'
            span_en = '<span lang=\"en\">'
            span_end = '</span>'

            mtl.text = html.escape(mtl.text)

            en = span_en + (mtl.text or '') + ''.join([lxml.html.tostring(child, encoding='unicode', method="html") for child in mtl.iterdescendants()]) + span_end
            ja = span_ja + (raw.text or '') + ''.join([lxml.html.tostring(child, encoding='unicode', method="html") for child in raw.iterdescendants()]) + span_end
            fill = ja + '<br>' + en

            if (raw.get('id') == mtl.get('id')) or (raw.get('class') == mtl.get('class')):
                new = re.sub(r'>(.+)<', '>' + fill + '<', lxml.html.tostring(raw, encoding='unicode'))
                new = lxml.html.fromstring(new)
                parent.replace(raw, new)

        merged_data = lxml.html.tostring(raw_html, encoding='unicode')

        return merged_data

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

    # Python code to sort the tuples using second element
    # of sublist Function to sort using sorted()
    def __sort(self, sub_li, reverse=False):

        # reverse = None (Sorts in Ascending order)
        # key is set to sort using second element of
        # sublist lambda has been used
        return (sorted(sub_li, key=lambda x: len(x[0]), reverse=reverse))
