import concurrent
import os
import itertools
import zlib
import concurrent.futures

from utils import download_file_from_url
import utils


def main(subs_list, out_path, max_workers=10, lines_to_skip=0):
    links_by_movie = {}
    with open(subs_list, 'r') as f:
        for line in map(lambda l: l.rstrip('\r\n'), utils.iterate_from_line(f, lines_to_skip)):
            imdb_id, s_num = line.split(':')
            for sub_link in map(lambda _: f.readline().rstrip('\r\n'), itertools.repeat(None, int(s_num))):
                links_by_movie[imdb_id] = sub_link.split('#')[1]

    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        jobs = [executor.submit(process_links, out_path + '/' + m_id, links) for m_id, links in links_by_movie.items()]
        for future in concurrent.futures.as_completed(jobs):
            try:
                future.result()
            except Exception as exc:
                print('An error occurred: {0}'.format(exc))


def process_links(movie_folder, links):
    print('{0}{1}'.format(movie_folder, links))
    os.makedirs(movie_folder, exist_ok=True)
    downloaded_files_paths = [download_file_from_url(link, movie_folder + '/' + link.split('/')[-1]) for link in links]
    for file in downloaded_files_paths:
        with open(file, 'rb') as sub_file, open(file.replace('.gz', ''), 'wb') as out_file:
            out_file.write(zlib.decompress(sub_file.read(), 16 + zlib.MAX_WBITS))

    return downloaded_files_paths


if __name__ == '__main__':
    main('data/os/subs_list.txt', 'data/os/subs', max_workers=1)
