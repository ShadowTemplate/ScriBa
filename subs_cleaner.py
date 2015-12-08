import itertools
import os
import glob
import constants


# Given the subtitles folder, this fun merges together subtitles of the same film that are divided into multiple CDs
# All the subtitles (.srt format) are filtered in order to keep only the text
def merge_subs(subs_folder):
    for folder in os.listdir(subs_folder):
        with open(subs_folder+'/'+folder+'/'+folder+'.txt', 'w') as out:
            for sub in glob.glob(subs_folder+'/'+folder+'/'+'*.srt'):
                with open(sub, 'r') as in_file:
                    for _ in itertools.repeat(None, 3):
                        in_file.readline()
                    for line in map(lambda l: l.rstrip('\r\n'), in_file):
                        if line == '':
                            for _ in itertools.repeat(None, 2):
                                in_file.readline()
                        else:
                            out.write(line+' ')
                os.remove(sub)


def main():
    merge_subs(constants.OS_SUBS_PATH)

if __name__ == '__main__':
    main()


