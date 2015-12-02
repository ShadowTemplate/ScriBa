from collections import defaultdict

from opensubtitles import OpenSubtitles
from utils import *


# TODO mutualize constants like user agent
# TODo assert number of links for subs = number of declared CD
# TODO check no duplicate ids in matched.txt


def main():
    with open('partial_matched.txt', 'r') as matched_movies_file, \
            open('partial_matched_subs.txt', 'w') as subs_list_file:
        user_agent = 'ScriBa v1.0'
        ids_per_request = 10
        lang = 'eng'

        os_client = OpenSubtitles()
        # token = '97s6gdka2flisf3u4l17afvm31'
        # os_client.set_token(token)
        token = os_client.login(user_agent=user_agent)
        print(token)

        lines_processed = 0
        movies_available = 0
        curr_request_ids = []
        for line in matched_movies_file:
            imdb_id = line.split(':')[1].rstrip('\r\n')
            curr_request_ids.append(imdb_id)

            if len(curr_request_ids) == ids_per_request:
                movies_found = find_matching_subs(os_client, subs_list_file, lang, curr_request_ids)
                movies_available += movies_found
                lines_processed += ids_per_request
                print('Processed {0} lines (total: {1}). Subtitles found for {2} movies (total {3})\n'
                      .format(ids_per_request, lines_processed, movies_found, movies_available))
                curr_request_ids = []

        if len(curr_request_ids) > 0:
            movies_found = find_matching_subs(os_client, subs_list_file, lang, curr_request_ids)
            movies_available += movies_found
            lines_processed += len(curr_request_ids)
            print('Processed {0} lines (total: {1}). Subtitles found for {2} movies (total {3})\n'
                  .format(len(curr_request_ids), lines_processed, movies_found, movies_available))


def find_matching_subs(os_client, subs_list_file, lang, curr_request_ids):
    print('Searching subtitles for id(s): {0}'.format(curr_request_ids))
    # data = os_client.search_subtitles_for_movies(curr_request_ids, lang)

    data = [s for s in os_client.search_subtitles_for_movies(curr_request_ids, lang)
            if s.get('IDMovieImdb') in [id.lstrip('0') for id in curr_request_ids]]

    subs_by_movie = defaultdict(list)
    for movie in data:
        subs_by_movie[movie.get('IDMovieImdb')].append(movie)  # group subtitles by movie

    report = ', '.join(['\'{0}\': {1}'.format(k, len(v)) for k, v in subs_by_movie.items()])
    print('Found {0} result(s): [{1}]'.format(len(data), report))

    print('Going to search and store the best subs for each movie...')
    best_subs_by_movie = [find_best_movie_subtitles(available_subs) for available_subs in subs_by_movie.values()]

    for movie_subs in best_subs_by_movie:
        prefix = '{0}:'.format(movie_subs[0].get('IDMovieImdb'))
        body = ','.join(['{0}:{1}'.format(sub.get('IDSubtitleFile'), sub.get('SubDownloadLink')) for sub in movie_subs])
        subs_list_file.write('{0}{1}\n'.format(prefix, body))
        print('{0} {1} link(s)'.format(prefix, len(movie_subs)))

    return len(best_subs_by_movie)


if __name__ == "__main__":
    main()
