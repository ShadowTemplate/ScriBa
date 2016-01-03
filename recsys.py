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

    def get_user_ratings(self, user, movie_to_skip=None):
        if user not in self.user_ratings:
            ratings = {}
            with open(constants.REC_SYS_RATINGS_BY_USER + user + '.txt', 'r') as movie_f:
                for line in filter(lambda l: l is not '', map(lambda l: l.rstrip('\r\n'), movie_f)):
                    movie, rating = line.split(',')
                    ratings[movie] = int(rating)
            self.user_ratings[user] = ratings
        return {movie: r for movie, r in self.user_ratings[user].items() if not movie_to_skip or movie_to_skip != movie}

    def get_movie_ratings(self, movie, user_to_skip=None):
        if movie not in self.movie_ratings:
            ratings = {}
            with open(constants.REC_SYS_RATINGS_BY_MOVIE + movie + '.txt', 'r') as movie_f:
                for line in filter(lambda l: l is not '', map(lambda l: l.rstrip('\r\n'), movie_f)):
                    user, rating = line.split(',')
                    ratings[user] = int(rating)
            self.movie_ratings[movie] = ratings
        return {user: r for user, r in self.movie_ratings[movie].items() if not user_to_skip or user_to_skip != user}

    def get_user_rating_for_movie(self, user, movie):
        return self.get_user_ratings(user)[movie]

    def get_user_avg_score(self, user):
        ratings = self.get_user_ratings(user)
        return sum(ratings.values()) / len(ratings) if len(ratings) else 0

    def get_user_relative_avg_score(self, user, relative, movie_to_skip=None):
        user_ratings = self.get_user_ratings(user, movie_to_skip=movie_to_skip)
        relative_ratings = self.get_user_ratings(relative, movie_to_skip=movie_to_skip)
        counter, items = 0, 0
        for movie, rating in user_ratings.items():
            if movie in relative_ratings:
                items += 1
                counter += user_ratings[movie]
        average = counter / items if items else 0
        return average

    def get_cos_similarity(self, user1, user2, movie_to_skip=None):
        user1_ratings = self.get_user_ratings(user1, movie_to_skip=movie_to_skip)
        user2_ratings = self.get_user_ratings(user2, movie_to_skip=movie_to_skip)
        numerator, norm1, norm2 = 0, 0, 0
        for movie, rating in user1_ratings.items():
            if movie in user2_ratings:
                numerator += user1_ratings[movie] * user2_ratings[movie]
                norm1 += user1_ratings[movie] ** 2
                norm2 += user2_ratings[movie] ** 2
        similarity = numerator / (sqrt(norm1) * sqrt(norm2)) if norm1 + norm2 > 0 else 0
        return similarity


def group_netflix_ratings_by_user():
    for movie in glob.glob(constants.NETFLIX_FULL_RATINGS_DATASET_PATH + '/*.txt'):
        with open(movie, 'r', encoding='ISO-8859-1') as in_file:
            curr_movie = in_file.readline().rstrip(':\r\n')
            for line in filter(lambda l: l is not '', map(lambda l: l.rstrip('\r\n'), in_file)):
                user, rating, _ = line.split(',')
                with open(constants.REC_SYS_RATINGS_BY_USER + user + '.txt', 'a', encoding='ISO-8859-1') as user_file:
                    user_file.write('{0},{1}\n'.format(curr_movie, int(rating)))


def group_netflix_ratings_by_movie():
    for movie in glob.glob(constants.NETFLIX_FULL_RATINGS_DATASET_PATH + '/*.txt'):
        with open(movie, 'r', encoding='ISO-8859-1') as in_file:
            curr_movie = in_file.readline().rstrip(':\r\n')
            for line in filter(lambda l: l is not '', map(lambda l: l.rstrip('\r\n'), in_file)):
                user, rating, _ = line.split(',')
                with open(constants.REC_SYS_RATINGS_BY_MOVIE + curr_movie + '.txt', 'a', encoding='ISO-8859-1') as \
                        movie_f:
                    movie_f.write('{0},{1}\n'.format(user, int(rating)))


def group_lens(output_f, error_f, test_set, cache):
    for movie, user in test_set:
        user_avg_score = cache.get_user_avg_score(user)
        movie_ratings = cache.get_movie_ratings(movie, user_to_skip=user)
        scores_sum, similarities_sum = 0, 0
        for corater, vote in movie_ratings.items():
            cos_similarity = cache.get_cos_similarity(user, corater, movie_to_skip=movie)
            corater_avg_score = cache.get_user_avg_score(corater)
            scores_sum += (vote - corater_avg_score) * cos_similarity
            similarities_sum += abs(cos_similarity)
        if similarities_sum:
            predicted_vote = user_avg_score + scores_sum / similarities_sum
            print('{0},{1},{2}'.format(movie, user, round(predicted_vote)))
            output_f.write('{0},{1},{2}\n'.format(movie, user, round(predicted_vote)))
        else:
            print('ERR: {0},{1}'.format(movie, user))
            error_f.write('{0},{1}\n'.format(movie, user))


def shw(output_f, error_f, test_set, cache):
    for movie, user in test_set:
        movie_ratings = cache.get_movie_ratings(movie, user_to_skip=user)
        num1, num2, norm = 0, 0, 0
        for corater, vote in movie_ratings.items():
            cos_similarity = cache.get_cos_similarity(user, corater, movie_to_skip=movie)
            num1 += abs(cos_similarity) * cache.get_user_relative_avg_score(user, corater)
            norm += abs(cos_similarity)
            num2 += cos_similarity * (vote - cache.get_user_relative_avg_score(corater, user))
        if norm:
            predicted_vote = num1 / norm + num2 / norm
            print('{0},{1},{2}'.format(movie, user, round(predicted_vote)))
            output_f.write('{0},{1},{2}\n'.format(movie, user, round(predicted_vote)))
        else:
            print('ERR: {0},{1}'.format(movie, user))
            error_f.write('{0},{1}\n'.format(movie, user))


def most_similar(output_f, error_f, test_set, cache):
    k_max = 5
    data = build_tfidf_matrix()
    movies_similarities = {}
    for movie, _ in test_set:
        if movie in data.movies_num_map and movie not in movies_similarities:
            movies_similarities[movie] = get_k_most_similar_movies(movie, data, k_max)

    for movie, user in test_set:
        if movie in data.movies_num_map:
            user_ratings = cache.get_user_ratings(user, movie_to_skip=movie)
            most_similar_vote = None
            for m_id, _ in movies_similarities[movie]:
                if m_id in user_ratings:
                    most_similar_vote = user_ratings[m_id]
                    break
            if most_similar_vote:
                print('{0},{1},{2}'.format(movie, user, most_similar_vote))
                output_f.write('{0},{1},{2}\n'.format(movie, user, most_similar_vote))
        else:
            print('ERR: {0},{1}'.format(movie, user))
            error_f.write('{0},{1}\n'.format(movie, user))


def load_test_set():
    print('Loading test set...')
    test_set, curr_movie = [], None
    with open(constants.NETFLIX_TEST_SET, 'r') as test_set_f:
        for line in filter(lambda l: l is not '', map(lambda l: l.rstrip('\r\n'), test_set_f)):
            if line.endswith(':'):
                curr_movie = line.rstrip(':')
            else:
                test_set.append((curr_movie, line))
    print('Test set requires {0} predictions.'.format(len(test_set)))
    return test_set


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

    algorithms = [group_lens, shw, most_similar]
    test_set = load_test_set()
    cache = Cache({}, {})
    for algorithm in algorithms:
        run_algorithm(algorithm, test_set, cache)


########################################################################################################################
def main_rec():
    print('Building documents and tf-idf matrix...')
    matrix = build_tfidf_matrix()
    print('Running prediction...')
    # lotr compagnia = '120737'
    # gladiator = '172495'
    get_k_most_similar_movies('120737', matrix, 3)
    print('\n\n')
    get_k_most_similar_movies('172495', matrix, 7)
########################################################################################################################


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
        k_most_similar.append((similar_id, cos_similarity))
    return k_most_similar

if __name__ == '__main__':
    main()
