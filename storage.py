import os
import glob
import re
from typing import List
import lxml
import csv

import natsort
from novel import Chapter
from novel import Novel


class Storage:

    MTL_ROOT_PATH: str
    RAW_ROOT_PATH: str
    RAW_OUTPUT_PATH: str
    MERGED_ROOT_PATH: str
    RAW_MATCH = re.compile(r"^(\d+)[-]([a-zA-Z\d\s_-]+)[-](.+)[.]([a-zA-Z0-9]{5,40})(.txt)?")
    BLOCK_MATCH = re.compile(r"^(\d+)[-](\d+)[.]([a-zA-Z\d\s_-]+)(.html)")

    def __init__(self, rawrootpath, rawoutputpath, mtlrootpath='', mergedrootpath='', wordlistpath=''):
        self.RAW_ROOT_PATH = rawrootpath
        self.RAW_OUTPUT_PATH = rawoutputpath
        self.MTL_ROOT_PATH = mtlrootpath
        self.MERGED_ROOT_PATH = mergedrootpath
        self.WORD_LIST_PATH = wordlistpath

    def get_raw_novel(self, name: str) -> Novel:
        novelpath = os.path.join(self.RAW_ROOT_PATH, name)
        if not os.path.exists(novelpath):
            return None
        chapters = []
        for file in natsort.natsorted(glob.glob(novelpath + "/*.txt", recursive=False)):
            matches = self.RAW_MATCH.match(str(os.path.split(file)[1]))
            groups = matches.groups()
            if len(groups) <= 1:
                continue

            with open(file, 'r', encoding='utf-8') as reader:
                data = reader.read()

            chapters.append(Chapter(groups[0], name, groups[2], data, groups[1], self.open_wordlist(name)))

        if os.path.exists(os.path.join(self.MTL_ROOT_PATH, name)):
            print("Translation Found for: " + name)
            chapters = self.__parse_mtl_novel(os.path.join(self.MTL_ROOT_PATH, name), name, chapters)

        return Novel(name, chapters)

    def load_all_raw(self) -> List[Novel]:
        folders = [f for f in glob.glob(self.RAW_ROOT_PATH + "*/", recursive=False)]
        novels: List[Novel] = []
        for folder in folders:
            novels.append(self.get_raw_novel(os.path.split(os.path.dirname(folder))[1]))

        return novels

    def store_raw_novel(self, novel: Novel):

        output = os.path.join(self.RAW_OUTPUT_PATH, novel.name)
        print('Store: ' + novel.name)
        if not os.path.exists(output):
            print("Create Output Folder for: " + novel.name)
            os.makedirs(output)
        elif os.path.isfile(output):
            raise IOError('File with the same Name already exist.')

        for chapter in novel.chapters:
            filename = "{id}-{name}-{chaptername}.html".format(id=chapter.chapterid, name=chapter.savename,
                                                               chaptername=chapter.name)
            with open(os.path.join(output, filename), 'w+', encoding='utf-8') as writer:
                writer.write(chapter.get_filtered_data())

    def store_all_raw_novel(self, novels: List[Novel]):

        for novel in novels:
            self.store_raw_novel(novel)

    def store_novel_as_block(self, novel: Novel, blocksize: int, merged=False):

        first_id = None
        last_id = None
        data = ''
        header = f"<!DOCTYPE html>\n<html>\n<head>\n<title>{novel.name} One Page</title>\n<meta charset=\"utf-8\"/>\n</head>\n<body>\n"
        footer = "</body>\n</html>"
        header_footer_size = header + footer
        header_footer_size = len(header_footer_size.encode('utf-8'))
        size = header_footer_size
        if not merged:
            novel_output_path = os.path.join(self.RAW_OUTPUT_PATH, novel.name)
        else:
            novel_output_path = os.path.join(self.MERGED_ROOT_PATH, novel.name)
        chapters_left = len(novel.chapters)

        if not os.path.exists(novel_output_path):
            print("Create Output Folder for: " + novel.name)
            os.makedirs(novel_output_path)
        elif os.path.isfile(novel_output_path):
            raise IOError('File with the same Name already exist.')

        for chapter in novel.chapters:
            if first_id is None:
                first_id = chapter.chapterid

            if not merged:
                data += chapter.get_filtered_data()
                size += chapter.size
            else:
                if chapter.merged_data is not None:
                    size += chapter.merged_size
                    data += chapter.merged_data
                else:
                    size += chapter.size
                    data += chapter.get_filtered_data()
            last_id = chapter.chapterid

            if size > blocksize or chapters_left == 1:
                filename = "{firstid}-{lastid}.{shortname}.html".format(firstid=first_id, lastid=last_id,
                                                                        shortname=chapter.savename)
                with open(os.path.join(novel_output_path, filename), 'w+', encoding='utf-8') as writer:
                    data = header + data + footer
                    writer.write(data)
                    data = ''
                    size = header_footer_size
                    first_id = None

            chapters_left -= 1

    def store_all_novel_as_block(self, novels: List[Novel], blocksize: int):
        for novel in novels:
            self.store_novel_as_block(novel, blocksize)

    def apply_word_list(self, novel_name: str, data: str):

        wordlist = self.open_wordlist(novel_name)

        if wordlist is None:
            return data

        for word in wordlist:
            data = data.replace(word[0], word[1])

        return data

    def open_wordlist(self, novel_name):

        wordlistpath = os.path.join(self.WORD_LIST_PATH, novel_name)

        if not os.path.exists(wordlistpath):
            return None
        replacements = []
        for file in natsort.natsorted(glob.glob(wordlistpath + "/*.tsv", recursive=False)):
            with open(file, 'r', encoding='utf-8') as reader:
                wordlist = csv.reader(reader, delimiter='\t', quotechar='|')

                for word in wordlist:
                    replacements.append(word)
        return replacements

    def __parse_mtl_novel(self, novelpath: str, novelname: str, raw_chapters: List[Chapter]) -> List[Chapter]:
        mtl_chapters = {}

        for file in natsort.natsorted(glob.glob(novelpath + "/*.html", recursive=False)):
            matches = self.BLOCK_MATCH.match(str(os.path.split(file)[1]))
            groups = matches.groups()
            if len(groups) < 4:
                continue

            with open(file, 'r', encoding='utf-8') as reader:
                mtl_data = reader.read()

            html = lxml.html.fromstring(mtl_data)
            tags = html.xpath("/html/body/div[@id]")
            for tag in tags:
                mtl_chapters[int(tag.get('id'))] = lxml.html.tostring(tag, encoding='unicode')

        for chapter in raw_chapters:
            chapter.mtl_data = mtl_chapters.get(int(chapter.chapterid), None)

        return raw_chapters
