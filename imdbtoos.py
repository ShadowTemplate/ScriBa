from collections import defaultdict

from opensubtitles import OpenSubtitles
from utils import *


# TODO mutualize constants like user agent

def retrieve_subtitles_from_list(input_file, output_file, ids_file):
    with open(input_file, 'r') as matched_movies_file, \
            open(output_file, 'w') as subs_list_file, open(ids_file, 'w') as ids_list_file:
        user_agent = 'ScriBa v1.0'
        ids_per_request = 10
        lang = 'eng'

        os_client = OpenSubtitles()
        token = os_client.login(user_agent=user_agent)
        print(token)

        lines_processed = 0
        movies_available = 0
        curr_request_ids = []
        for line in matched_movies_file:
            imdb_id = line.split(':')[1].rstrip('\r\n')
            curr_request_ids.append(imdb_id)

            if len(curr_request_ids) == ids_per_request:
                movies_found = find_matching_subs(os_client, subs_list_file, ids_list_file, lang, curr_request_ids)
                movies_available += movies_found
                lines_processed += ids_per_request
                print('Processed {0} lines (total: {1}). Subtitles found for {2} movies (total {3})\n'
                      .format(ids_per_request, lines_processed, movies_found, movies_available))
                curr_request_ids = []

        if len(curr_request_ids) > 0:
            movies_found = find_matching_subs(os_client, subs_list_file, ids_list_file, lang, curr_request_ids)
            movies_available += movies_found
            lines_processed += len(curr_request_ids)
            print('Processed {0} lines (total: {1}). Subtitles found for {2} movies (total {3})\n'
                  .format(len(curr_request_ids), lines_processed, movies_found, movies_available))

        os_client.logout()


def find_matching_subs(os_client, subs_list_file, ids_list_file, lang, curr_request_ids):
    print('Searching subtitles for id(s): {0}'.format(curr_request_ids))
    # data = os_client.search_subtitles_for_movies(curr_request_ids, lang)

    resp = os_client.search_subtitles_for_movies(curr_request_ids, lang)

    # if one of the input imdb_id corresponds to a TV series, the response may contain useless entries (episodes subs)
    # these subs can be easily detected (the imdb_id is in the attribute 'SeriesIMDBParent' instead of 'IDMovieImdb')
    data = [s for s in resp if s.get('IDMovieImdb') in [i.lstrip('0') for i in curr_request_ids]]  # filter subs

    subs_by_movie = defaultdict(list)
    for movie in data:
        subs_by_movie[movie.get('IDMovieImdb')].append(movie)  # group subtitles by movie

    report = ', '.join(['\'{0}\': {1}'.format(k, len(v)) for k, v in subs_by_movie.items()])
    print('Found {0} result(s): [{1}]'.format(len(data), report))

    print('Going to search and store the best subs for each movie...')
    best_subs_by_movie = [find_best_movie_subtitles(available_subs) for available_subs in subs_by_movie.values()]

    for movie_subs in best_subs_by_movie:
        movie_id = movie_subs[0].get('IDMovieImdb')
        prefix = '{0}:{1}'.format(movie_id, len(movie_subs))
        body = '\n'.join(['{0}#{1}'.format(s.get('IDSubtitleFile'), s.get('SubDownloadLink')) for s in movie_subs])
        subs_list_file.write('{0}\n{1}\n'.format(prefix, body))
        ids_list_file.write('{0}\n'.format(movie_id))
        print('{0} link(s)'.format(prefix, len(movie_subs)))

    return len(best_subs_by_movie)


def dedupe_lines_by_imdb_id(input_file, output_file):
    ids_map = {}
    with open(input_file, 'r') as f:
        for line in f:
            entry_id = line.split(':')[1].rstrip('\r\n')
            if ids_map.get(entry_id):
                print('Found multiple lines for id {0}. They will be removed.'.format(entry_id))
                ids_map.pop(entry_id)
            else:
                ids_map[entry_id] = line

    with open(output_file, 'w') as clean_f:
        for line in sorted(ids_map.values(), key=lambda item: (len(item), item)):  # length-wise sorting
            clean_f.write(line)

    print('All duplicated entries have been deleted.')


def main():
    input_file = 'data/imdb/matched.txt'
    cleaned_input_file = 'data/imdb/clean_matched.txt'
    dedupe_lines_by_imdb_id(input_file, cleaned_input_file)
    output_file = 'data/os/subs_list.txt'
    ids_file = 'data/os/ids_list.txt'
    retrieve_subtitles_from_list(cleaned_input_file, output_file, ids_file)


if __name__ == "__main__":
    main()
