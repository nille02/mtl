import os
import glob
import re
from typing import List
import lxml
import csv

import natsort
import unicodedata

from novel import Chapter
from novel import Novel


class Storage:

    RAW_ROOT_PATH: str
    RAW_OUTPUT_PATH: str
    RAW_MATCH = re.compile(r"^(\d+)[-]([a-zA-Z\d\s_-]+)[-](.+)[.]([a-zA-Z0-9]{5,40})(\.txt)?")
    BLOCK_MATCH = re.compile(r"^(\d+)[-](\d+)[.]([a-zA-Z\d\s_-]+)(.html)")

    def __init__(self, rawrootpath: str, rawoutputpath: str, wordlistpath=''):
        self.RAW_ROOT_PATH = rawrootpath
        self.RAW_OUTPUT_PATH = rawoutputpath
        self.WORD_LIST_PATH = wordlistpath

    def get_raw_novel(self, name: str) -> Novel:
        novelpath = os.path.join(self.RAW_ROOT_PATH, name)
        if not os.path.exists(novelpath):
            raise IOError('Novel not Found.')
        chapters = []
        wordlist = self.open_wordlist(name)

        for file in natsort.natsorted(glob.glob(novelpath + "/*.txt", recursive=False)):
            matches = self.RAW_MATCH.match(str(os.path.split(file)[1]))
            groups = matches.groups()
            if len(groups) <= 1:
                continue

            with open(file, 'r', encoding='utf-8') as reader:
                data = reader.read()

            chapters.append(Chapter(int(groups[0]), name, groups[2], data, groups[1], wordlist))

        return Novel(name, chapters, wordlist=wordlist)

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
            filename = f"{chapter.chapterid}-{chapter.savename}-{chapter.name}.html"
            with open(os.path.join(output, filename), 'w+', encoding='utf-8') as writer:
                writer.write(chapter.get_filtered_data())

    def store_all_raw_novel(self, novels: List[Novel]):

        for novel in novels:
            self.store_novel_as_block(novel, 1, True)

    def store_novel_as_block(self, novel: Novel, blocksize: int, generate_index: bool = False):

        first_id = None
        last_id = None
        data = ''
        header = f"<!DOCTYPE html>\n<html>\n<head>\n<title>{novel.name}</title>\n<meta charset=\"utf-8\"/>\n" \
            f"<meta name=\"viewport\" content=\"width=device-width; initial-scale=1; maximum-scale=1\">\n" \
            f"<link rel=\"stylesheet\" href=\"../styles.css\">\n</head>\n<body>"
        footer = "\n<script language='javascript' type='text/javascript' src='../page.js'></script>\n</body>\n</html>"
        header_footer_size = header + footer

        header_footer_size = len(header_footer_size.encode('utf-8'))
        size = header_footer_size

        novel_output_path = os.path.join(self.RAW_OUTPUT_PATH, novel.name)
        chapters_left = len(novel.chapters)

        if not os.path.exists(novel_output_path):
            print("Create Output Folder for: " + novel.name)
            os.makedirs(novel_output_path)
        elif os.path.isfile(novel_output_path):
            raise IOError('File with the same Name already exist.')

        write_queue = []

        for chapter in novel.chapters:
            if first_id is None:
                first_id = chapter.chapterid

            data += chapter.get_filtered_data()
            size += chapter.size

            last_id = chapter.chapterid

            if size > blocksize or chapters_left == 1:
                if first_id == last_id:
                    if chapter.chapter_number == "":
                        filename = f"{first_id}.{chapter.savename}.html"
                    else:
                        filename = f"{first_id}.{chapter.savename}-{self.__clean_filename(chapter.chapter_number)}.html"
                else:
                    filename = f"{first_id}-{last_id}.{chapter.savename}.html"

                write_queue.append({"filename": filename,
                                    "data": data,
                                    "first_id": first_id})
                data = ''
                size = header_footer_size
                first_id = None

            chapters_left -= 1

        # Write all chapters from the write queue and add back and forward links
        for i in range(len(write_queue)):

            toc_header = "\n<div id='toc' style='text-align:center'>"
            toc_footer = "<a id='togoogle' target='_self' style='display:none'>To Google Translate</a></div>\n"
            toc_line = ""

            if generate_index:
                if i == 0:
                    toc_line = f"<a href='index.html'>TOC</a> | " \
                               f"<a href='{write_queue[i+1]['filename']}'>Next -&gt;</a><br>"
                elif i == (len(write_queue) - 1):
                    toc_line = f"<a href='{write_queue[i-1]['filename']}'>&lt;- Previous</a> | " \
                               f"<a href='index.html'>TOC</a><br>"
                else:
                    toc_line = f"<a href='{write_queue[i-1]['filename']}'>&lt;- Previous</a> | " \
                               f"<a href='index.html'>TOC</a> | <a href='{write_queue[i+1]['filename']}'>Next -&gt;</a><br>"
                if novel.name == "Death Mage Raw":
                    toc_footer += "<div>Special thanks to MBA and the Users from the LBN #spoilers Discord. " \
                                  "Without them this would not be possible.</div>"
            toc = toc_header + toc_line + toc_footer
            with open(os.path.join(novel_output_path, write_queue[i]['filename']), 'w+', encoding='utf-8') as writer:
                write_queue[i]['data'] = header.replace("<html>", "<html lang=\"ja\">") + toc + "<hr>\n" + write_queue[i]['data'] + "\n<hr>" + toc + footer
                writer.write(write_queue[i]['data'])

        # Generate Index
        if generate_index:
            index_header = f"<h1>{novel.name} Index</h1><br><ul style='list-style-type:none;'>\n"
            index_footer = "\n</ul>"
            index = ""

            for entry in write_queue:
                name = entry['filename'].replace(".html", "")
                name = name.strip("_")
                index = f"<li><a href='{entry['filename']}' target='_blank'>{name}</a></li>\n" + index

            index = index_header + index + index_footer
            with open(os.path.join(novel_output_path, "index.html"), 'w+', encoding='utf-8') as writer:
                index = header + index + footer
                writer.write(index)

    def store_all_novel_as_block(self, novels: List[Novel], blocksize: int):
        for novel in novels:
            self.store_novel_as_block(novel, blocksize)

    def open_wordlist(self, novel_name: str) -> List:

        wordlistpath = os.path.join(self.WORD_LIST_PATH, novel_name)

        if not os.path.exists(wordlistpath):
            return []
        replacements = []
        for file in natsort.natsorted(glob.glob(wordlistpath + "/*.tsv", recursive=False)):
            with open(file, 'r', encoding='utf-8') as reader:
                wordlist = csv.reader(reader, delimiter='\t', quotechar='|')
                for word in wordlist:
                    replacements.append(word)

        return self.__sort(replacements, reverse=True)

    @staticmethod
    def __clean_filename(filename, replace=' '):
        blacklist = "|*/\\%&$§!?=<>:\""
        char_limit = 210
        # replace spaces
        for r in replace:
            filename = filename.replace(r, '_')

        # keep only valid ascii chars
        cleaned_filename = unicodedata.normalize('NFKD', filename)

        # remove blacklistet chars
        cleaned_filename = ''.join(c for c in cleaned_filename if c not in blacklist)
        if len(cleaned_filename) > char_limit:
            print(f"Warning, filename truncated because it was over {char_limit}. Filenames may no longer be unique")
        return cleaned_filename[:char_limit]

    # Python code to sort the tuples using first element
    # of sublist Function to sort using sorted()
    @staticmethod
    def __sort(sub_li, reverse=False):

        # reverse = None (Sorts in Ascending order)
        # key is set to sort using first element of
        # sublist lambda has been used
        return sorted(sub_li, key=lambda x: len(x[0]), reverse=reverse)
