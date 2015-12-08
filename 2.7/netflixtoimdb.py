#!/usr/bin/python2.7

from itertools import dropwhile

from imdb import IMDb


def get_id_from_title(imdb, title, year):
    results = imdb.search_movie(title)
    print('Query \'{0}\' [{1}] returned {2} item(s)'.format(title, year, len(results)))
    same_year_movies = [dict(m.data, **{'id': m.movieID}) for m in results if m.data.get('year') == year]
    print('Found {0} item(s) having same year as input\n'.format(len(same_year_movies)))
    return same_year_movies


def convert_netflix_to_imdb_ids(netflix_file, matched_file, no_match_file, conflict_file, lines_to_skip=0):
    imdb_client = IMDb()
    with open(netflix_file, 'r') as netflix_f, open(matched_file, 'a') as matched_f, \
            open(no_match_file, 'a') as no_match_f, open(conflict_file, 'a') as conflict_f:
        lines_processed, error_lines, matched_num, no_match_num, conflict_num = [0, 0, 0, 0, 0]
        for line in (l.rstrip('\r\n') for i, l in dropwhile(lambda x: x[0] < lines_to_skip, enumerate(netflix_f))):
            try:
                year, title = int(line.split(',')[1]), ','.join(line.split(',')[2:])
                result = get_id_from_title(imdb_client, title, year)
                matches = len(result)
                if matches == 0:
                    no_match_f.write('{0}'.format(line))
                    no_match_num += 1
                elif matches == 1:
                    matched_f.write('{0},{1}'.format(result[0].get('id'), line))
                    matched_num += 1
                else:
                    conflicting_ids = '/'.join([movie.get('id') for movie in result])
                    conflict_f.write('{0},{1}'.format(conflicting_ids, line))
                    conflict_num += 1

                print('Processed: {0}'.format(line))
                lines_processed += 1
            except ValueError as e:
                print('Error at line {0}: {1}{2}'.format(lines_to_skip + lines_processed + 1, line, e))
                error_lines += 1
                continue
            except Exception as e:
                print('Error at line {0}: {1}{2}'.format(lines_to_skip + lines_processed + 1, line, e))
                break

        print('\nLines processed: {0}\nLines poorly formatted: {1}\nMatched: {2}\nNot matching: {3}\nConflicting: {4}'
              .format(lines_processed, error_lines, matched_num, no_match_num, conflict_num))


def main():
    project_data_folder = '/home/gianvito/PycharmProjects/ScriBa/'
    convert_netflix_to_imdb_ids(project_data_folder + 'data/netflix/movie_titles.txt',
                                project_data_folder + 'data/imdb/match.txt',
                                project_data_folder + 'data/imdb/no-match.txt',
                                project_data_folder + 'data/imdb/conflict.txt')


if __name__ == "__main__":
    main()
