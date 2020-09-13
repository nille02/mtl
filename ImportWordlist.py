import os
import glob
import csv
import requests
import json
import unicodedata


def ignore_keyword(entry: str, translation: str):  # We ignore some Keywords that helps to understand who is talking but translation gets more troubblesome with them.
    blacklist = ["WARERA", "WAREWARE", "WARE", "WATAKUSHI", "SESSHA", "BOKU", "WASHI", "ATASHI", "WATASHI",
                 "nanoyo", "degozaru", "degozaruna", "degozaruyo", "degozaruka", "nojana", "jarou", "nojazo", "nojaga",
                 "desuka", "nojarou", "noja", "nojayo", "Boya", "Umu", "ja！", "joo", "juu", "ussu", "ssu", "oneself",
                 "Kannushi", "WAREWA", "faith", "Rival", "Shogun", "Aniki", "KISAMA", "vertical drill", "otouto"
                 ]
    for word in blacklist:
        if word == entry or word == translation:
            return True
    return False


def clean_filename(filename, replace=' '):
    blacklist = "|*/\\%&$§!?=<>:\""
    char_limit = 210
    # replace spaces
    for r in replace:
        filename = filename.replace(r, '_')

    # keep only valid ascii chars
    cleaned_filename = unicodedata.normalize('NFKD', filename)

    # remove blacklisted chars
    cleaned_filename = ''.join(c for c in cleaned_filename if c not in blacklist)
    if len(cleaned_filename) > char_limit:
        print(f"Warning, filename truncated because it was over {char_limit}. Filenames may no longer be unique")
    return cleaned_filename[:char_limit]


def main():

    novels = [{"id": "1",  # The id is the category id and not the novel id. I should use the DICTIONARYS URL to get them
              "name": "Death Mage Raw"},
              {"id": "41",
               "name": "Clearing an Isekai with the Zero-Believers Goddess Raw"}
              ]

    OUTPUT_DIRECTORY = os.path.join(os.getcwd(), 'data/wordlist')

    NOVEL_URL = "http://mtl.maikoengelke.com/api/novel"  # Returns full novel List
    DICTIONARYS = "http://mtl.maikoengelke.com/api/dictionary/"  # Return the List of dictionary's for the given Novel
    CATEGORY = "http://mtl.maikoengelke.com/api/category/"  # Return the category's of the selected dictionary
    KEYWORDS = "http://mtl.maikoengelke.com/api/entry/"  # Returns the Keyword list of the selected category id

    for novel in novels:
        OUTPUT = os.path.join(OUTPUT_DIRECTORY, novel.get("name"))
        r = requests.get(url=CATEGORY + novel.get("id"))
        categories = r.json()
        print(f"Save wordlist for: {novel.get('name')}")
        for category in categories:
            request_wordlist = requests.get(url=KEYWORDS+str(category['id']))   # Returns the current Wordlist from the current category
            print('\tSaving: ' + category['name'])
            category['name'] = clean_filename(category['name'])                 # Replace Chars that are not allowed in filenames
            output = os.path.join(OUTPUT, ('MBA-' + category['name'] + '.tsv'))
            with open(output, 'w+', encoding='utf-8') as writer:
                for keyword in request_wordlist.json():
                    if ignore_keyword(keyword['entryOriginal'], keyword['entryTranslation']):  # Exclude Blacklist
                        continue
                    if keyword['entryOriginal'] == '-' and keyword['entryTranslation'] == '-':  # If we find just a '-', its a deleted Keyword
                        continue
                    if keyword['description'] is None:
                        line = f"{keyword['entryOriginal']}\t{keyword['entryTranslation']}\n"
                    else:
                        line = f"{keyword['entryOriginal']}\t{keyword['entryTranslation']}\t{keyword['description']}\n"

                    writer.writelines(line)


if __name__ == "__main__":
    main()
