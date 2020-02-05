import os
import storage
import novel
import re
import lxml.html


def convert_death_mage_chapter_title(chapter: novel.Chapter) -> novel.Chapter:
    content = lxml.html.fromstring(chapter.data)
    for headline in content.xpath("//p[contains(@class,'novel_subtitle')]"):
        text = headline.text.split("　", 1)
        if text[0].startswith("第"):
            text[0] = text[0].replace("第", "")
        if len(text) == 2:
            if text[0] == "序章":
                text[0] = "Prologue:"
                chapter.chapter_name = text[0]
            if text[0].startswith("閑話"):
                side_chapter = text[0].split("閑話", 1)
                if len(side_chapter) == 2:
                    if side_chapter[1] != "":
                        text[0] = "Side Chapter {number}: ".format(number=convert_ja_numbers_to_latin(side_chapter[1]))
                        chapter.chapter_name = text[0]
                    else:
                        text[0] = "Side Chapter:"
                        chapter.chapter_name = text[0]
            if text[0].endswith("話"):
                chapter_number = text[0].replace("話", "")
                text[0] = "Chapter {number}: ".format(number=str(convert_written_ja_number_to_latin(chapter_number)))
                chapter.chapter_name = text[0]
        headline.text = " ".join(text)

    chapter.data = lxml.html.tostring(content, encoding='unicode')
    return chapter


def convert_ja_numbers_to_latin(text: str) -> str:
    new_name = ""
    for char in text:
        if char == "０":
            char = "0"
        if char == "１":
            char = "1"
        if char == "２":
            char = "2"
        if char == "３":
            char = "3"
        if char == "４":
            char = "4"
        if char == "５":
            char = "5"
        if char == "６":
            char = "6"
        if char == "７":
            char = "7"
        if char == "８":
            char = "8"
        if char == "９":
            char = "9"
        new_name += char
    return new_name


def convert_written_ja_number_to_latin(text: str) -> int:
    number = 0
    if len(text) == 5:
        if text[1] == "百":
            number = 100 * return_single_ja_sign_to_number(text[0])
            text = text[2:]
    if len(text) == 4:
        if text.startswith("百"):
            number = 100
            text = text[1:]
        if text[1] == "百":
            number = 100 * return_single_ja_sign_to_number(text[0])
            number += return_double_ja_sign_to_number(str(text[2] + text[3]))
    if len(text) == 3:
        if text[1] == "十":
            number += return_double_ja_sign_to_number(str(text[0] + text[1]))
            number += return_single_ja_sign_to_number(text[2])
        if text[0] == "百":
            number = 100 + return_double_ja_sign_to_number(str(text[1] + text[2]))
        if text[1] == "百":
            number += 100 * return_single_ja_sign_to_number(text[0])
            number += return_single_ja_sign_to_number(text[2])
    if len(text) == 2:
        if text.startswith("十") or text.endswith("十"):
            number = return_double_ja_sign_to_number(text)
        if text.startswith("百") or text.endswith("百"):
            number = return_double_ja_sign_to_number(text)
    if len(text) == 1:
        number = return_single_ja_sign_to_number(text)

    return number


def return_single_ja_sign_to_number(text: str) -> int:
    number = 0
    if text == "一":
        number = 1
    if text == "二":
        number = 2
    if text == "三":
        number = 3
    if text == "四":
        number = 4
    if text == "五":
        number = 5
    if text == "六":
        number = 6
    if text == "七":
        number = 7
    if text == "八":
        number = 8
    if text == "九":
        number = 9
    if text == "十":
        number = 10
    if text == "百":
        number = 100
    return number


def return_double_ja_sign_to_number(text: str) -> int:
    number = 0
    if text.startswith("十"):
        number = 10 + return_single_ja_sign_to_number(text[1])
    if text.endswith("十") and not text.startswith("百"):
        number = 10 * return_single_ja_sign_to_number(text[0])
    if text.startswith("百"):
        number = 100 + return_single_ja_sign_to_number(text[1])
    if text.endswith("百"):
        number = 100 * return_single_ja_sign_to_number(text[0])
    return number


input_path = "E:\\Niels\\Documents\\GitHub\\urlchanges\\SyosetuIndex"

path = input_path

output = os.path.join(os.getcwd(), 'data/output/')
wordlist = os.path.join(os.getcwd(), 'data/wordlist/')

storage = storage.Storage(path, output, wordlist)

if True:
    print("Death Mage Raw")
    novel = storage.get_raw_novel('Death Mage Raw')

    for dm_chapters in novel.chapters:
        dm_chapters = convert_death_mage_chapter_title(dm_chapters)

    storage.store_novel_as_block(novel, 1)
    # storage.store_novel_as_block(novel, 10000000000)

if False:
    print("Immortal Adventurer")
    novel2 = storage.get_raw_novel('Immortal Adventurer')
    storage.store_novel_as_block(novel2, 1)
    # storage.store_novel_as_block(novel2, 1000000000)

if False:
    print("mom Please Do not come for adventure Raw")
    novel2 = storage.get_raw_novel('mom Please Do not come for adventure Raw')
    storage.store_novel_as_block(novel2, 1)
    storage.store_novel_as_block(novel2, 1000000000)

if False:
    print("Tondemo Skill de Isekai Hourou Meshi Raw")
    novel3 = storage.get_raw_novel('Tondemo Skill de Isekai Hourou Meshi Raw')
    for tondemo_chapter in novel3.chapters:
        tondemo_chapter = convert_death_mage_chapter_title(tondemo_chapter)
        pass
    # storage.store_novel_as_block(novel3, 1000000000)
    storage.store_novel_as_block(novel3, 1)
