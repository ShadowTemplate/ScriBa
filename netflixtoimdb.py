from imdb import IMDb


def get_id_from_title(imdb, title, year):
    assert title and year
    results = imdb.search_movie(title)
    print('Query \'{0}\' [{1}] returned {2} item(s)'.format(title, year, len(results)))
    same_year_movies = [dict(movie.data, **{'id': movie.movieID}) for movie in results if
                        movie.data.get('year') == year]
    matches = len(same_year_movies)
    print('Found {0} item(s) having same year as input\n'.format(matches))
    return same_year_movies


def main(lines_to_skip):
    imdb_client = IMDb()
    with open('data/netflix/movie_titles.txt', 'r') as in_file, open('data/imdb/matched.txt', 'a') as matched_file, \
            open('data/imdb/nomatch.txt', 'a') as no_match_file, open('data/imdb/conflict.txt', 'a') as conflict_file:

        lines_processed, error_lines, matched_num, no_match_num, conflict_num = [0, 0, 0, 0, 0]
        remaining_lines_to_skip = lines_to_skip
        for line in in_file:
            if remaining_lines_to_skip > 0:
                remaining_lines_to_skip -= 1
                continue

            try:
                splits = line.split(',')
                netflix_id = splits[0]
                year = int(splits[1])
                title = ','.join(splits[2:]).rstrip('\r\n')

                result = get_id_from_title(imdb_client, title, year)
                matches = len(result)
                if matches == 0:
                    no_match_file.write('{0}'.format(line))
                    no_match_num += 1
                elif matches == 1:
                    matched_file.write('{0},{1}'.format(result[0].get('id'), line))
                    matched_num += 1
                else:
                    conflicting_ids = '/'.join([movie.get('id') for movie in result])
                    conflict_file.write('{0},{1}'.format(conflicting_ids, line))
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


if __name__ == "__main__":
    main(0)
