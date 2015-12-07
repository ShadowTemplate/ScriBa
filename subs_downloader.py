import concurrent
import concurrent.futures
import itertools
import os
import zlib

import utils


def download_subs_from_list(subs_list, out_path, max_workers=10, lines_to_skip=0):
    links_by_movie = {}
    with open(subs_list, 'r') as f:
        for line in map(lambda l: l.rstrip('\r\n'), utils.iterate_from_line(f, lines_to_skip)):
            imdb_id, s_num = line.split(':')
            links_iter = map(lambda _: f.readline().rstrip('\r\n').split('#')[1], itertools.repeat(None, int(s_num)))
            links_by_movie[imdb_id] = [link for link in links_iter]

    successes, errors = [], []
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        jobs = {executor.submit(process_links, out_path + '/' + m_id, ls): m_id for m_id, ls in links_by_movie.items()}
        for future_job in concurrent.futures.as_completed(jobs.keys()):
            try:
                successes.append(future_job.result())
            except Exception as exc:
                print('An error occurred while processing subtitle(s) for movie {0}: {1}'.format(jobs[future_job], exc))
                errors.append(jobs[future_job])

    return successes, errors


def process_links(movie_folder, links):
    os.makedirs(movie_folder, exist_ok=True)
    decompressed_files = []
    for link in links:
        print('Downloading and decompressing: {0}'.format(link))
        sub_file_name = movie_folder + '/' + link.split('/')[-1].replace('.gz', '')
        with utils.urllib.request.urlopen(link) as sub_data, open(sub_file_name, 'wb') as out_file:
            out_file.write(zlib.decompress(sub_data.read(), 16 + zlib.MAX_WBITS))
        decompressed_files.append(sub_file_name)

    return decompressed_files


def main():
    successes, errors = download_subs_from_list('data/os/subs_list_soft.txt', 'data/os/subs', max_workers=4)
    print('Successes:\n{0}\n\nErrors:{1}'.format(successes, errors))


if __name__ == '__main__':
    main()
