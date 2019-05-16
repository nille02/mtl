import os
import glob
import re
import lxml.html
import utils
import natsort

import storage


print("My Tests")

path = os.path.join(os.getcwd(), 'data/novels/')
output = os.path.join(os.getcwd(), 'data/output/')
mtl = os.path.join(os.getcwd(), 'data/mtl/')
merged = os.path.join(os.getcwd(), 'data/merged/')
wordlist = os.path.join(os.getcwd(), 'data/wordlist/')

storage = storage.Storage(path, output, mtl, merged, wordlist)

#novels = storage.load_all_raw()
novel = storage.get_raw_novel('Death Mage Raw')

#print("Test: " + novel.chapters[1].merged_data)

storage.store_raw_novel(novel)


#storage.store_all_raw_novel(novels)

print("Generate Full Version")
storage.store_novel_as_block(novel, 100000000, False)

#storage.store_all_novel_as_block(novels, 1000000)

print('\a')
exit(0)
