import glob
import os
from math import sqrt

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import linear_kernel

import constants


class Cache(object):
    def __init__(self, user_ratings, movie_ratings):
        self.user_ratings = user_ratings
        self.movie_ratings = movie_ratings

    def get_user_ratings(self, user, movie_to_skip_id=None):
        if user not in self.user_ratings:
            ratings = {}
            with open(constants.REC_SYS_RATINGS_BY_USER + user + '.txt', 'r') as movie_f:
                for line in filter(lambda l: l is not '', map(lambda l: l.rstrip('\r\n'), movie_f)):
                    netflix_movie_id, rating = line.split(',')
                    ratings[netflix_movie_id] = int(rating)
            self.user_ratings[user] = ratings
        return {m: r for m, r in self.user_ratings[user].items() if not movie_to_skip_id or movie_to_skip_id != m}

    def get_movie_ratings(self, netflix_movie_id, user_to_skip=None):
        if netflix_movie_id not in self.movie_ratings:
            ratings = {}
            with open(constants.REC_SYS_RATINGS_BY_MOVIE + netflix_movie_id + '.txt', 'r') as movie_f:
                for line in filter(lambda l: l is not '', map(lambda l: l.rstrip('\r\n'), movie_f)):
                    user, rating = line.split(',')
                    ratings[user] = int(rating)
            self.movie_ratings[netflix_movie_id] = ratings
        return {u: r for u, r in self.movie_ratings[netflix_movie_id].items() if not user_to_skip or user_to_skip != u}

    def get_user_rating_for_movie(self, user, movie):
        return self.get_user_ratings(user)[movie]

    def get_user_avg_score(self, user):
        ratings = self.get_user_ratings(user)
        return sum(ratings.values()) / len(ratings) if len(ratings) else 0

    def get_user_relative_avg_score(self, user, relative, movie_to_skip_id=None):
        user_ratings = self.get_user_ratings(user, movie_to_skip_id=movie_to_skip_id)
        relative_ratings = self.get_user_ratings(relative, movie_to_skip_id=movie_to_skip_id)
        counter, items = 0, 0
        for netflix_movie_id, rating in user_ratings.items():
            if netflix_movie_id in relative_ratings:
                items += 1
                counter += user_ratings[netflix_movie_id]
        average = counter / items if items else 0
        return average

    def get_cos_similarity(self, user1, user2, movie_to_skip=None):
        user1_ratings = self.get_user_ratings(user1, movie_to_skip_id=movie_to_skip)
        user2_ratings = self.get_user_ratings(user2, movie_to_skip_id=movie_to_skip)
        numerator, norm1, norm2 = 0, 0, 0
        for netflix_movie_id, rating in user1_ratings.items():
            if netflix_movie_id in user2_ratings:
                numerator += user1_ratings[netflix_movie_id] * user2_ratings[netflix_movie_id]
                norm1 += user1_ratings[netflix_movie_id] ** 2
                norm2 += user2_ratings[netflix_movie_id] ** 2
        similarity = numerator / (sqrt(norm1) * sqrt(norm2)) if norm1 + norm2 > 0 else 0
        return similarity


def group_netflix_ratings_by_user():
    for netflix_movie_id_file in glob.glob(constants.NETFLIX_FULL_RATINGS_DATASET_PATH + '/*.txt'):
        with open(netflix_movie_id_file, 'r', encoding='ISO-8859-1') as in_file:
            curr_netflix_movie_id = in_file.readline().rstrip(':\r\n')
            for line in filter(lambda l: l is not '', map(lambda l: l.rstrip('\r\n'), in_file)):
                user, rating, _ = line.split(',')
                with open(constants.REC_SYS_RATINGS_BY_USER + user + '.txt', 'a', encoding='ISO-8859-1') as user_file:
                    user_file.write('{0},{1}\n'.format(curr_netflix_movie_id, int(rating)))


def group_netflix_ratings_by_movie():
    for netflix_movie_id_file in glob.glob(constants.NETFLIX_FULL_RATINGS_DATASET_PATH + '/*.txt'):
        with open(netflix_movie_id_file, 'r', encoding='ISO-8859-1') as in_file:
            curr_netflix_movie_id = in_file.readline().rstrip(':\r\n')
            for line in filter(lambda l: l is not '', map(lambda l: l.rstrip('\r\n'), in_file)):
                user, rating, _ = line.split(',')
                with open(constants.REC_SYS_RATINGS_BY_MOVIE + curr_netflix_movie_id + '.txt', 'a',
                          encoding='ISO-8859-1') as movie_f:
                    movie_f.write('{0},{1}\n'.format(user, int(rating)))


def group_lens(output_f, error_f, test_set, cache):
    for netflix_movie_id, user in test_set:
        user_avg_score = cache.get_user_avg_score(user)
        movie_ratings = cache.get_movie_ratings(netflix_movie_id, user_to_skip=user)
        scores_sum, similarities_sum = 0, 0
        for corater, vote in movie_ratings.items():
            cos_similarity = cache.get_cos_similarity(user, corater, movie_to_skip=netflix_movie_id)
            corater_avg_score = cache.get_user_avg_score(corater)
            scores_sum += (vote - corater_avg_score) * cos_similarity
            similarities_sum += abs(cos_similarity)
        if similarities_sum:
            predicted_vote = user_avg_score + scores_sum / similarities_sum
            print('{0},{1},{2}'.format(netflix_movie_id, user, round(predicted_vote)))
            output_f.write('{0},{1},{2}\n'.format(netflix_movie_id, user, round(predicted_vote)))
        else:
            print('ERR: {0},{1}'.format(netflix_movie_id, user))
            error_f.write('{0},{1}\n'.format(netflix_movie_id, user))


def shw(output_f, error_f, test_set, cache):
    for netflix_movie_id, user in test_set:
        movie_ratings = cache.get_movie_ratings(netflix_movie_id, user_to_skip=user)
        num1, num2, norm = 0, 0, 0
        for corater, vote in movie_ratings.items():
            cos_similarity = cache.get_cos_similarity(user, corater, movie_to_skip=netflix_movie_id)
            num1 += abs(cos_similarity) * cache.get_user_relative_avg_score(user, corater)
            norm += abs(cos_similarity)
            num2 += cos_similarity * (vote - cache.get_user_relative_avg_score(corater, user))
        if norm:
            predicted_vote = num1 / norm + num2 / norm
            print('{0},{1},{2}'.format(netflix_movie_id, user, round(predicted_vote)))
            output_f.write('{0},{1},{2}\n'.format(netflix_movie_id, user, round(predicted_vote)))
        else:
            print('ERR: {0},{1}'.format(netflix_movie_id, user))
            error_f.write('{0},{1}\n'.format(netflix_movie_id, user))


def most_similar(output_f, error_f, test_set, cache):
    k_max = 25
    data = build_tfidf_matrix()
    movies_similarities = {}
    imdb_ids_map, netflix_ids_map = get_netflix_imdb_matching()
    for netflix_movie_id, _ in test_set:
        if netflix_movie_id in netflix_ids_map:
            imdb_id = netflix_ids_map[netflix_movie_id]
            if imdb_id in data.movies_num_map and imdb_id not in movies_similarities:
                movies_similarities[imdb_id] = get_k_most_similar_movies(imdb_id, data, k_max)

    print('Loaded {} similarities...'.format(len(movies_similarities)))

    for netflix_movie_id, user in test_set:
        if netflix_movie_id in netflix_ids_map and netflix_ids_map[netflix_movie_id] in data.movies_num_map:
            imdb_id = netflix_ids_map[netflix_movie_id]
            # user_ratings = cache.get_user_ratings(user, movie_to_skip_id=netflix_movie_id)
            user_ratings = get_user_ratings_no_cache(user, movie_to_skip_id=netflix_movie_id)
            most_similar_vote = None
            for imdb_m_id, _ in movies_similarities[imdb_id]:
                if imdb_m_id in imdb_ids_map and imdb_ids_map[imdb_m_id] in user_ratings:
                    most_similar_vote = user_ratings[imdb_ids_map[imdb_m_id]]
                    break
            if most_similar_vote:
                # print('{0},{1},{2}'.format(netflix_movie_id, user, most_similar_vote))
                output_f.write('{0},{1},{2}\n'.format(netflix_movie_id, user, most_similar_vote))
            else:
                # print('ERR: {0},{1}'.format(netflix_movie_id, user))
                error_f.write('{0},{1}\n'.format(netflix_movie_id, user))
        else:
            # print('ERR: {0},{1}'.format(netflix_movie_id, user))
            error_f.write('{0},{1}\n'.format(netflix_movie_id, user))


def load_test_set(test_set_file):
    print('Loading test set...')
    test_set, curr_movie = [], None
    with open(test_set_file, 'r') as test_set_f:
        for line in filter(lambda l: l is not '', map(lambda l: l.rstrip('\r\n'), test_set_f)):
            if line.endswith(':'):
                curr_movie = line.rstrip(':')
            else:
                test_set.append((curr_movie, line))
    print('Test set requires {0} predictions.'.format(len(test_set)))
    return test_set


def get_netflix_imdb_matching():
    imdb_ids_map, netflix_ids_map = {}, {}  # {imdb_id: netflix_id}, {netflix_id: imdb_id}
    with open(constants.IMDB_MATCHED, 'r') as match_f:
        for line in map(lambda l: l.rstrip('\r\n'), match_f):
            imdb_id = line.split(',')[0].lstrip('0')
            netflix_id = line.split(',')[1]
            imdb_ids_map[imdb_id] = netflix_id
            netflix_ids_map[netflix_id] = imdb_id
    return imdb_ids_map, netflix_ids_map


def generate_os_test_set(limit=None):
    print('Building test set...')
    imdb_ids_map, _ = get_netflix_imdb_matching()
    counter = 0
    with open(constants.OS_IDS_LIST, 'r') as ids_list_f, open(constants.SCRIBA_TEST_SET, 'w') as test_set_f:
        for imdb_movie_id in map(lambda l: l.rstrip('\r\n'), ids_list_f):
            test_set_f.write('{0}:\n'.format(imdb_ids_map[imdb_movie_id]))
            with open(constants.REC_SYS_RATINGS_BY_MOVIE + imdb_ids_map[imdb_movie_id] + '.txt', 'r') as movie_f:
                for line in map(lambda l: l.rstrip('\r\n'), movie_f):
                    user, _ = line.split(',')
                    test_set_f.write('{0}\n'.format(user))
                    counter += 1
                    if limit and counter >= limit:
                        print('Test set built.')
                        return
    print('Test set built.')
    return


def compute_rmse(predictions_f, rmse_f, cache):
    counter, sum_squared_values = 0, 0
    for line in filter(lambda l: l is not '', map(lambda l: l.rstrip('\r\n'), predictions_f)):
        movie, user, prediction = line.split(',')
        delta = cache.get_user_rating_for_movie(user, movie) - int(prediction)
        counter += 1
        sum_squared_values += delta * delta
    rmse_f.write(str(sqrt(sum_squared_values / counter) if counter else 0))


def run_algorithm(algorithm_function, test_set, cache):
    os.makedirs(constants.REC_SYS_OUTPUT_PATH, exist_ok=True)
    algorithm_name = algorithm_function.__name__
    print('Running algorithm: {0}'.format(algorithm_name))
    prefix = constants.REC_SYS_OUTPUT_PATH + algorithm_name
    output_file = prefix + '.res.txt'
    with open(output_file, 'w') as output_f, open(prefix + '.err.txt', 'w') as error_f:
        algorithm_function(output_f, error_f, test_set, cache)
    print('Computing RMSE for algorithm: {0}'.format(algorithm_name))
    with open(output_file, 'r') as predictions_f, open(prefix + '.rmse.txt', 'w') as rmse_f:
        compute_rmse(predictions_f, rmse_f, cache)


def main():
    if not os.path.exists(constants.REC_SYS_RATINGS_BY_USER):
        os.makedirs(constants.REC_SYS_RATINGS_BY_USER, exist_ok=True)
        print('Building ratings_by_user map...')
        group_netflix_ratings_by_user()
        print('Map built')

    if not os.path.exists(constants.REC_SYS_RATINGS_BY_MOVIE):
        os.makedirs(constants.REC_SYS_RATINGS_BY_MOVIE, exist_ok=True)
        print('Building ratings_by_movie map...')
        group_netflix_ratings_by_movie()
        print('Map built')

    # generate_recent_test_set(2000, 2008)
    algorithms = [most_similar]
    test_set = load_test_set(constants.RECENT_TEST_SET)
    cache = Cache({}, {})
    for algorithm in algorithms:
        run_algorithm(algorithm, test_set, cache)


class TfidfMatrix(object):
    def __init__(self, documents, movies_ids_list, movies_num_map, tfidf):
        self.documents = documents
        self.movies_ids_list = movies_ids_list
        self.movies_num_map = movies_num_map
        self.tfidf = tfidf


def build_tfidf_matrix():
    documents = []
    movies_ids_list = []  # [imdb_id]
    movies_num_map = {}  # imdb_id, doc_num
    with open(constants.OS_IDS_LIST, 'r') as ids_list_f:
        for count, m_id in enumerate(map(lambda l: l.rstrip('\r\n'), ids_list_f)):
            documents.append(build_movie_doc(m_id))
            movies_ids_list.append(m_id)
            movies_num_map[m_id] = count

    tfidf = TfidfVectorizer(stop_words='english').fit_transform(documents)
    return TfidfMatrix(documents, movies_ids_list, movies_num_map, tfidf)


def build_movie_doc(m_id):
    with open(constants.OS_SUBS_PATH_MERGED + m_id + '.txt', 'r', encoding='ISO-8859-1') as script_f:
        content = script_f.read()
    if os.path.exists(constants.IMDB_PLOTS_SYNOPSES + m_id + '.txt'):
        with open(constants.IMDB_PLOTS_SYNOPSES + m_id + '.txt', 'r', encoding='ISO-8859-1') as plots_f:
            content += plots_f.read()
    return content


def get_k_most_similar_movies(m_id, rec_data, k=5):
    documents, ids_list, index = rec_data.documents, rec_data.movies_ids_list, rec_data.movies_num_map[m_id]
    cosine_similarities = linear_kernel(rec_data.tfidf[index: index + 1], rec_data.tfidf).flatten()
    # print('Unsorted similarities: {0}'.format(cosine_similarities))
    related_docs_indices = cosine_similarities.argsort()[: -(k + 2): -1]
    # print('Ranking (indexes):\n{0}'.format(related_docs_indices))
    # print('Sorted similarities: {0}'.format(cosine_similarities[related_docs_indices]))
    k_most_similar = []
    # print('\nMost similar movies:')
    for i in range(len(related_docs_indices) - 1):
        similar_id = related_docs_indices[i + 1]
        cos_similarity = cosine_similarities[related_docs_indices[i + 1]]
        # print('{0} - IMDb id: {1} - Plot: {2}'.format(i + 1, ids_list[similar_id], documents[similar_id]))
        # print('{0} - IMDb id: {1} - Similarity: {2}'.format(i + 1, ids_list[similar_id], cos_similarity))
        k_most_similar.append((str(similar_id), cos_similarity))
    return k_most_similar


def generate_recent_test_set(from_year, to_year, limit=None):
    print('Extracting recent movies...')
    recent_movies = {}
    with open(constants.IMDB_MATCHED, 'r') as match_f:
        for _, netflix_movie_id, year, _ in map(lambda l: l.split(',', maxsplit=3), match_f):
            if from_year <= int(year) < to_year:
                recent_movies[year] = recent_movies.get(year, []) + [netflix_movie_id]

    for k, v in recent_movies.items():
        print('{0}: {1} movies'.format(k, len(v)))
    # list(map(print, ['{0}: {1} movies'.format(k, len(v)) for k, v in recent_movies.items()]))

    print('Building test set...')
    imdb_ids_map, netflix_ids_map = get_netflix_imdb_matching()
    predictions_num, movies_involved = 0, 0
    with open(constants.OS_IDS_LIST, 'r') as ids_list_f, open(constants.RECENT_TEST_SET, 'w') as test_set_f:
        available = set()
        for imdb_movie_id in map(lambda l: l.rstrip('\r\n'), ids_list_f):
            available.add(imdb_movie_id)

        for netflix_movie_id in filter(lambda m: netflix_ids_map[m] in available, sum(recent_movies.values(), [])):
            movies_involved += 1
            test_set_f.write('{0}:\n'.format(netflix_movie_id))
            with open(constants.REC_SYS_RATINGS_BY_MOVIE + netflix_movie_id + '.txt', 'r') as movie_f:
                for line in map(lambda l: l.rstrip('\r\n'), movie_f):
                    user, _ = line.split(',')
                    test_set_f.write('{0}\n'.format(user))
                    predictions_num += 1
                    if limit and predictions_num >= limit:
                        print('Test set built: {0} predictions for {1} movies'.format(predictions_num, movies_involved))
                        return
    print('Test set built: {0} predictions for {1} movies'.format(predictions_num, movies_involved))
    return


def get_user_ratings_no_cache(user, movie_to_skip_id=None):
    ratings = {}
    with open(constants.REC_SYS_RATINGS_BY_USER + user + '.txt', 'r') as movie_f:
        for line in filter(lambda l: l is not '', map(lambda l: l.rstrip('\r\n'), movie_f)):
            netflix_movie_id, rating = line.split(',')
            ratings[netflix_movie_id] = int(rating)
    return {m: r for m, r in ratings.items() if not movie_to_skip_id or movie_to_skip_id != m}


if __name__ == '__main__':
    main()

