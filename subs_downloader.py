import concurrent
import concurrent.futures
import itertools
import os
import urllib.request
import time
from enum import Enum
from collections import OrderedDict

from stem import Signal
from stem.control import Controller

import constants
import utils


class ItemType(Enum):
    SUB_ID = 0
    SUB_LINK = 1

    @staticmethod
    def get_processor(item_type):
        if item_type == ItemType.SUB_ID:
            return process_ids
        if item_type == ItemType.SUB_LINK:
            return process_links


class TorDownloader(metaclass=utils.Singleton):
    __curr_ip = None

    @staticmethod
    def get_anonymous_urllib():
        if not TorDownloader.__curr_ip:
            TorDownloader.refresh_ip()
        print('Tor urllib has IP: {0}'.format(TorDownloader.__curr_ip))
        return urllib.request

    @staticmethod
    def refresh_ip():
        print('Going to refresh Tor IP...\nOld Tor IP: {0}'.format(TorDownloader.__curr_ip))
        time.sleep(constants.TOR_REFRESH_TIMEOUT)  # the signal may fail if not sent with an appropriate delay
        with Controller.from_port(port=constants.TOR_PORT) as controller:
            controller.authenticate(password=constants.TOR_PASSWORD)
            controller.signal(Signal.NEWNYM)
        proxy_support = urllib.request.ProxyHandler({'http': '127.0.0.1:8118', 'https': '127.0.0.1:8118'})
        urllib.request.install_opener(urllib.request.build_opener(proxy_support))
        TorDownloader.__curr_ip = utils.get_external_ip(lib=urllib.request)
        print('New Tor IP: {0}'.format(TorDownloader.__curr_ip))


def build_items_to_download_map(subs_list_file, lines_to_skip, index):
    movies_map = OrderedDict()
    with open(subs_list_file, 'r') as subs_list_f:
        for line in map(lambda l: l.rstrip('\r\n'), utils.iterate_after_dropping(subs_list_f, lines_to_skip)):
            imdb_id, s_num = line.split(':')
            item_iter = map(lambda _: subs_list_f.readline().split('#')[index], itertools.repeat(None, int(s_num)))
            movies_map[imdb_id] = [item.rstrip('\r\n') for item in item_iter]
    return movies_map


def download_subs_from_list(subs_list_file, out_path, item_type, lines_to_skip=0, max_workers=1):
    items_map, successes, errors = build_items_to_download_map(subs_list_file, lines_to_skip, item_type.value), {}, {}

    if max_workers == 1:
        for m_id, items in items_map.items():
            try:
                successes[m_id] = process_links(out_path + m_id, items)
            except Exception as exc:
                print('An error occurred while processing movie {0}: {1}'.format(m_id, exc))
                errors[m_id] = exc
    else:
        processor = ItemType.get_processor(item_type)
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            # build a dictionary of {future_job : imdb_id}
            jobs = {executor.submit(processor, out_path + m_id, items): m_id for m_id, items in items_map.items()}
            for future_job in concurrent.futures.as_completed(jobs.keys()):
                try:
                    successes[jobs[future_job]] = future_job.result()
                except Exception as exc:
                    print('An error occurred while processing movie {0}: {1}'.format(jobs[future_job], exc))
                    errors[jobs[future_job]] = exc
    return successes, errors


def process_links(movie_folder, links):
    decompressed_files = []
    print('{0} files expected in folder {1}'.format(len(links), movie_folder))
    for link in links:
        sub_file_name = movie_folder + '/' + link.split('/')[-1].replace('.gz', '.srt')
        sub_data = None
        while not sub_data:
            print('Going to download: {0}'.format(link))
            try:
                sub_data = utils.download_file_from_url(link, lib=TorDownloader.get_anonymous_urllib())
            except urllib.error.HTTPError as exc:
                print('An error occurred while processing subtitle {0}: {1}'.format(sub_file_name, exc))
                if exc.code == 410:
                    print('Download limit reached: a new IP is required. Tor IP will be changed and operation retried.')
                    TorDownloader.refresh_ip()

        os.makedirs(movie_folder, exist_ok=True)
        print('Going to decompress: {0}\n'.format(sub_file_name))
        with open(sub_file_name, 'wb') as out_file:
            out_file.write(utils.decompress_gzip(sub_data))
        decompressed_files.append(sub_file_name)
    return decompressed_files


def process_ids(movie_folder, ids):
    decompressed_files = []
    print('{0} files expected in folder {1}'.format(len(ids), movie_folder))
    client = utils.ScriBa.get_client()
    for s_id in ids:
        sub_file_name = movie_folder + '/' + s_id + '.srt'
        sub_data = None
        while not sub_data:
            print('Going to download: {0}'.format(s_id))
            try:
                sub_data = client.download_subtitles([s_id])
            except urllib.error.HTTPError as exc:
                print('An error occurred while processing subtitle {0}: {1}'.format(sub_file_name, exc))
                if exc.code == 410:
                    print('Download limit reached: a new IP is required. Tor IP will be changed and operation retried.')
                    TorDownloader.refresh_ip()

        os.makedirs(movie_folder, exist_ok=True)
        print('Going to decompress: {0}\n'.format(sub_file_name))
        with open(sub_file_name, 'wb') as out_file:
            out_file.write(utils.get_sub_from_encoded_data(sub_data[0].get('data')))
        decompressed_files.append(sub_file_name)
    return decompressed_files


def main():
    successes, errors = download_subs_from_list(constants.OS_SUBS_LIST, constants.OS_SUBS_PATH, ItemType.SUB_LINK)
    print('Successes:\n{0}\n\nErrors:\n{1}'.format(successes, errors))


if __name__ == '__main__':
    main()
