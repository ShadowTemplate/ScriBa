import concurrent
import concurrent.futures
import itertools
import os

import utils


def download_subs_from_list(subs_list, out_path, lines_to_skip=0, max_workers=10):
    links_by_movie, successes, errors = {}, {}, {}
    with open(subs_list, 'r') as f:
        for line in map(lambda l: l.rstrip('\r\n'), utils.iterate_after_dropping(f, lines_to_skip)):
            imdb_id, s_num = line.split(':')
            links_iter = map(lambda _: f.readline().rstrip('\r\n').split('#')[1], itertools.repeat(None, int(s_num)))
            links_by_movie[imdb_id] = [link for link in links_iter]

    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        jobs = {executor.submit(process_links, out_path + m_id, ls): m_id for m_id, ls in links_by_movie.items()}
        for future_job in concurrent.futures.as_completed(jobs.keys()):
            try:
                successes[jobs[future_job]] = future_job.result()
            except Exception as exc:
                print('An error occurred while processing subtitle(s) for movie {0}: {1}'.format(jobs[future_job], exc))
                errors[jobs[future_job]] = exc
    return successes, errors


def process_links(movie_folder, links):
    os.makedirs(movie_folder, exist_ok=True)
    decompressed_files = []
    for link in links:
        print('Downloading and decompressing: {0}'.format(link))
        sub_file_name = movie_folder + '/' + link.split('/')[-1].replace('.gz', '')
        with open(sub_file_name, 'wb') as out_file:
            out_file.write(utils.decompress_gzip(utils.download_file_from_url(link)))
        decompressed_files.append(sub_file_name)
    return decompressed_files


def main():
    successes, errors = download_subs_from_list('data/os/subs_list_soft.txt', 'data/os/subs/', max_workers=14)
    print('Successes:\n{0}\n\nErrors:\n{1}'.format(successes, errors))


if __name__ == '__main__':
    main()
