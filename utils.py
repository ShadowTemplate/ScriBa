import hashlib
from itertools import dropwhile
import zlib
import base64
import urllib.request

from opensubtitles import OpenSubtitles


class Singleton(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


class ScriBa(metaclass=Singleton):
    __os_client = OpenSubtitles()

    @staticmethod
    def get_client():
        if not ScriBa.__os_client.is_connected():
            print('OpenSubtitles client disconnected. Logging in...')
            print('Token: {0}'.format(ScriBa.__os_client.login(user_agent='ScriBa v1.0')))
        return ScriBa.__os_client


def iterate_after_dropping(iterable, elements_to_drop):
    return (l for i, l in dropwhile(lambda x: x[0] < elements_to_drop, enumerate(iterable)))


def get_sub_from_encoded_data(encoded_data):
    return decompress_gzip(base64.b64decode(encoded_data))


def get_md5(file_path):
    return hashlib.md5(open(file_path, 'rb').read()).hexdigest()  # memory inefficient, but ok for small files, like srt


def download_file_from_url(url):
    with urllib.request.urlopen(url) as response:
        return response.read()


def decompress_gzip(data):
    return zlib.decompress(data, 16 + zlib.MAX_WBITS)

# Given a IMDB ID return a list of dictionaries.
# Each dictionary contains the IDSubtitleFile and the SubDownloadLink


# TODO assert number of links for subs = number of declared CDs
def find_best_movie_subtitles(movie_subs):
    # Sort data by SubSumCD value
    sorted_data = sorted(movie_subs, key=lambda k: k['SubSumCD'])
    # Subtitles from the same CD-set have dame IDSubtitle but different IDSubtitleFile (sequential)
    # Keep the IDSubtitle of the subtitle with lower SubSumCD
    best_sub_id = sorted_data[0]['IDSubtitle']

    # Create and fill the final list
    return [{'IDSubtitleFile': sub['IDSubtitleFile'], 'SubDownloadLink': sub['SubDownloadLink'],
             'IDMovieImdb': sub['IDMovieImdb']} for sub in sorted_data if sub['IDSubtitle'] == best_sub_id]
