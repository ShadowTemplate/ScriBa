import itertools
import os
import glob
import re

from bs4 import BeautifulSoup

import constants
import utils


# Given the subtitles folder, this fun merges together subtitles of the same film that are divided into multiple CDs
# All the subtitles (.srt format) are filtered in order to keep only the text
def merge_subs(subs_folder, subs_folder_merged):
    os.makedirs(subs_folder_merged, exist_ok=True)
    for folder in os.listdir(subs_folder):
        print('Processing folder: {0}'.format(folder))
        with open(subs_folder_merged + '/' + folder + '.txt', 'w') as out:
            for sub in glob.glob(subs_folder + '/' + folder + '/*.srt'):
                with open(sub, 'r', encoding='ISO-8859-1') as in_file:
                    for line in map(lambda l: l.rstrip('\r\n'), utils.iterate_after_dropping(in_file, 3)):
                        if line == '':
                            for _ in itertools.repeat(None, 2):
                                in_file.readline()
                        else:
                            if re.search('<(.*?)>', line):
                                bs = BeautifulSoup(line, 'lxml')
                                out.write(bs.get_text() + ' ')
                            else:
                                out.write(line + ' ')


def main():
    merge_subs(constants.OS_SUBS_PATH, constants.OS_SUBS_PATH_MERGED)

if __name__ == '__main__':
    main()
