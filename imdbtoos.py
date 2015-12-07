from collections import defaultdict

from utils import *
import utils


def find_subs_links_from_ids_list(source_file, subs_links_file, movies_with_subs_list_file, lines_to_skip=0,
                                  ids_per_request=10, lang='eng', os_client=utils.ScriBa.get_client()):
    with open(source_file, 'r') as source_f, open(subs_links_file, 'w') as subs_links_f, \
            open(movies_with_subs_list_file, 'w') as movies_with_subs_list_f:
        pending_ids = []
        movies_found = 0
        lines_iter = enumerate(map(lambda l: l.rstrip('\r\n'), utils.iterate_after_dropping(source_f, lines_to_skip)))
        for count, imdb_id in map(lambda p: (p[0], p[1].split(',')[0]), lines_iter):
            pending_ids.append(imdb_id)
            if count and not count % ids_per_request:
                movies_found += find_matching_subs(os_client, pending_ids, lang, subs_links_f, movies_with_subs_list_f)
                lines_to_skip += ids_per_request
                print('Processed {0} lines. Found subtitles for {1} movies\n'.format(lines_to_skip, movies_found))
                pending_ids = []

        if pending_ids:
            movies_found += find_matching_subs(os_client, pending_ids, lang, subs_links_f, movies_with_subs_list_f)
            lines_to_skip += len(pending_ids)
            print('Processed {0} lines. Found subtitles for {1} movies\n'.format(lines_to_skip, movies_found))


def find_matching_subs(os_client, request_ids, lang, subs_links_f, movies_with_subs_list_f):
    print('Searching subtitles for id(s): {0}'.format(request_ids))
    resp = os_client.search_subtitles_for_movies(request_ids, lang)
    subs_by_movie = defaultdict(list)
    # if one of the input imdb_id corresponds to a TV series, the response may contain useless entries (episodes subs)
    # these subs can be easily detected (the imdb_id is in the attribute 'SeriesIMDBParent' instead of 'IDMovieImdb')
    # data = [s for s in resp if s.get('IDMovieImdb') in [i.lstrip('0') for i in request_ids]] TODO check below & remove
    stripped_ids = [i.lstrip('0') for i in request_ids]
    for movie in filter(lambda sub: sub.get('IDMovieImdb') in stripped_ids, resp):
        subs_by_movie[movie.get('IDMovieImdb')].append(movie)  # group subtitles by movie

    report = ', '.join(['\'{0}\': {1}'.format(k, len(v)) for k, v in subs_by_movie.items()])
    print('Found {0} result(s): [{1}]'.format(sum(list(map(lambda x: len(x), subs_by_movie.values()))), report))

    print('Going to search and store the best subs for each movie...')
    best_subs_by_movie = [find_best_movie_subtitles(available_subs) for available_subs in subs_by_movie.values()]

    for movie_subs in filter(lambda subs: subs, best_subs_by_movie):  # filter out movies without subs
        movie_id = movie_subs[0].get('IDMovieImdb')
        movie_header = '{0}:{1}'.format(movie_id, len(movie_subs))
        links = '\n'.join(['{0}#{1}'.format(s.get('IDSubtitleFile'), s.get('SubDownloadLink')) for s in movie_subs])
        subs_links_f.write('{0}\n{1}\n'.format(movie_header, links))
        movies_with_subs_list_f.write('{0}\n'.format(movie_id))
        print('{0} link(s)'.format(movie_header, len(movie_subs)))
    return len(best_subs_by_movie)


def deduplicate_lines_by_id(ids_list_file, unique_ids_list_file):
    ids_map = {}
    with open(ids_list_file, 'r') as ids_list_f:
        for entry_id in map(lambda l: l.split(',')[0], ids_list_f):
            if ids_map.get(entry_id):
                ids_map[entry_id] += 1
            else:
                ids_map[entry_id] = 1

    with open(unique_ids_list_file, 'w') as unique_ids_list_f:
        unique_items = [imdb_id for imdb_id, occurrences in ids_map.items() if ids_map[imdb_id] == 1]
        unique_ids_list_f.write('\n'.join(sorted(unique_items, key=lambda item: (len(item), item))))  # sort length-wise

    print('All duplicated entries have been deleted')


def main():
    ids_list_file, unique_ids_list_file = constants.IMDB_MATCHED, constants.IMDB_UNIQUE_MATCHED
    deduplicate_lines_by_id(ids_list_file, unique_ids_list_file)
    subs_links_file, movies_with_subs_list_file = constants.OS_SUBS_LIST, constants.OS_IDS_LIST
    find_subs_links_from_ids_list(unique_ids_list_file, subs_links_file, movies_with_subs_list_file)


if __name__ == "__main__":
    main()
