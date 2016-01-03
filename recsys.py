import glob
import os
from math import sqrt

import klepto
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import linear_kernel

import constants


def group_netflix_ratings_by_user(ratings_folder, output_folder):
    for movie in glob.glob(ratings_folder + '/*.txt'):
        with open(movie, 'r', encoding='ISO-8859-1') as in_file:
            curr_movie = in_file.readline().rstrip(':\r\n')
            for line in filter(lambda l: l is not '', map(lambda l: l.rstrip('\r\n'), in_file)):
                user, rating, _ = line.split(',')
                with open(output_folder + user + '.txt', 'a', encoding='ISO-8859-1') as user_file:
                    user_file.write('{0},{1}\n'.format(curr_movie, int(rating)))


def group_netflix_ratings_by_movie(ratings_folder, output_folder):
    for movie in glob.glob(ratings_folder + '/*.txt'):
        with open(movie, 'r', encoding='ISO-8859-1') as in_file:
            curr_movie = in_file.readline().rstrip(':\r\n')
            for line in filter(lambda l: l is not '', map(lambda l: l.rstrip('\r\n'), in_file)):
                user, rating, _ = line.split(',')
                with open(output_folder + curr_movie + '.txt', 'a', encoding='ISO-8859-1') as movie_file:
                    movie_file.write('{0},{1}\n'.format(user, int(rating)))


def get_user_ratings(ratings_by_user_path, user, movie_to_skip=None):
    ratings = {}
    with open(ratings_by_user_path + user + '.txt', 'r') as movie_f:
        for line in filter(lambda l: l is not '', map(lambda l: l.rstrip('\r\n'), movie_f)):
            movie, rating = line.split(',')
            if not movie_to_skip or movie_to_skip != movie:
                ratings[movie] = int(rating)
    return ratings


def get_movie_ratings(ratings_by_movie_path, movie, user_to_skip=None):
    ratings = []
    with open(ratings_by_movie_path + movie + '.txt', 'r') as movie_f:
        for line in filter(lambda l: l is not '', map(lambda l: l.rstrip('\r\n'), movie_f)):
            user, rating = line.split(',')
            if not user_to_skip or user_to_skip != user:
                ratings.append((user, int(rating)))
    return ratings


def get_user_rating_for_movie(ratings_by_user_path, user, movie):
    with open(ratings_by_user_path + user + '.txt', 'r') as user_f:
        for line in filter(lambda l: l is not '', map(lambda l: l.rstrip('\r\n'), user_f)):
            m, rating = line.split(',')
            if m == movie:
                return int(rating)


def get_user_avg_score(ratings_by_user_path, user, cache=None):
    if cache and user in cache:
        return cache[user]

    ratings = get_user_ratings(ratings_by_user_path, user)
    average = sum(ratings.values()) / len(ratings) if len(ratings) else 0
    cache[user] = average
    return average


def get_user_relative_avg_score(ratings_by_user_path, user, relative, movie_to_skip=None, cache=None):
    if cache and user + '.' + relative in cache:
        return cache[user + '.' + relative]

    user_ratings = get_user_ratings(ratings_by_user_path, user, movie_to_skip=movie_to_skip)
    relative_ratings = get_user_ratings(ratings_by_user_path, relative, movie_to_skip=movie_to_skip)
    counter, items = 0, 0
    for movie, rating in user_ratings.items():
        if movie in relative_ratings:
            items += 1
            counter += user_ratings[movie]
    average = counter / items if items else 0
    cache[user + '.' + relative] = average
    return average


def get_cos_similarity(user1, user2, ratings_by_user_path, movie_to_skip=None, cache=None):
    key = '-'.join(sorted([user1, user2]))
    if cache and key in cache:
        return cache[key]

    user1_ratings = get_user_ratings(ratings_by_user_path, user1, movie_to_skip=movie_to_skip)
    user2_ratings = get_user_ratings(ratings_by_user_path, user2, movie_to_skip=movie_to_skip)
    numerator, norm1, norm2 = 0, 0, 0
    for movie, rating in user1_ratings.items():
        if movie in user2_ratings:
            numerator += user1_ratings[movie] * user2_ratings[movie]
            norm1 += user1_ratings[movie] ** 2
            norm2 += user2_ratings[movie] ** 2
    similarity = numerator / (sqrt(norm1) * sqrt(norm2)) if norm1 + norm2 > 0 else 0
    cache[key] = similarity
    return similarity


def group_lens(output_file, error_file, test_set, ratings_by_movie_path, ratings_by_user_path):
    with open(output_file, 'w') as output_f, open(error_file, 'w') as error_f:
        users_similarities, users_avg_scores = {}, {}
        for movie, user in test_set:
            user_avg_score = get_user_avg_score(ratings_by_user_path, user, cache=users_avg_scores)
            movie_ratings = get_movie_ratings(ratings_by_movie_path, movie, user_to_skip=user)
            scores_sum, similarities_sum = 0, 0
            for corater, vote in movie_ratings:
                cos_similarity = get_cos_similarity(user, corater, ratings_by_user_path,
                                                    movie_to_skip=movie, cache=users_similarities)
                corater_avg_score = get_user_avg_score(ratings_by_user_path, corater, cache=users_avg_scores)
                scores_sum += (vote - corater_avg_score) * cos_similarity
                similarities_sum += abs(cos_similarity)
            if similarities_sum:
                predicted_vote = user_avg_score + scores_sum / similarities_sum
                output_f.write('{0},{1},{2}\n'.format(movie, user, round(predicted_vote)))
            else:
                error_f.write('{0},{1}\n'.format(movie, user))


def shw(output_file, error_file, test_set, ratings_by_movie_path, ratings_by_user_path):
    with open(output_file, 'w') as output_f, open(error_file, 'w') as error_f:
        users_similarities, users_avg_scores, users_realtive_avg_scores = {}, {}, {}
        for movie, user in test_set:
            movie_ratings = get_movie_ratings(ratings_by_movie_path, movie, user_to_skip=user)
            num1, num2, norm = 0, 0, 0
            for corater, vote in movie_ratings:
                cos_similarity = get_cos_similarity(user, corater, ratings_by_user_path,
                                                    movie_to_skip=movie, cache=users_similarities)
                num1 += abs(cos_similarity) * get_user_relative_avg_score(ratings_by_user_path, user, corater,
                                                                          cache=users_realtive_avg_scores)
                norm += abs(cos_similarity)
                num2 += cos_similarity * (vote - get_user_relative_avg_score(ratings_by_user_path, corater, user,
                                                                             cache=users_realtive_avg_scores))
            if norm:
                predicted_vote = num1 / norm + num2 / norm
                output_f.write('{0},{1},{2}\n'.format(movie, user, round(predicted_vote)))
            else:
                error_f.write('{0},{1}\n'.format(movie, user))


def most_similar(output_file, error_file, test_set, ratings_by_movie_path, ratings_by_user_path):
    k_max = 5
    data = build_tfidf_matrix(constants.OS_IDS_LIST, constants.OS_SUBS_PATH_MERGED, constants.IMDB_PLOTS_SYNOPSES)  # TODO: remove

    with open(output_file, 'w') as output_f, open(error_file, 'w') as error_f:
        for movie, user in test_set:
            if movie in data.indexes:
                similar_movies = get_k_most_similar_movies(movie, data, k_max)
                user_ratings = get_user_ratings(ratings_by_user_path, user, movie_to_skip=movie)
                most_similar_vote = None
                for m_id, _ in similar_movies:
                    if m_id in user_ratings:
                        most_similar_vote = user_ratings[m_id]
                        break
                if most_similar_vote:
                    output_f.write('{0},{1},{2}\n'.format(movie, user, most_similar_vote))
                    continue
            error_f.write('{0},{1}\n'.format(movie, user))


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


def compute_rmse(predictions_file, rmse_file, ratings_by_user_path):
    counter, sum_squared_values = 0, 0
    with open(predictions_file, 'r') as predictions_f:
        for line in filter(lambda l: l is not '', map(lambda l: l.rstrip('\r\n'), predictions_f)):
            movie, user, prediction = line.split(',')
            delta = get_user_rating_for_movie(ratings_by_user_path, user, movie) - int(prediction)
            counter += 1
            sum_squared_values += delta * delta
    with open(rmse_file, 'w') as rmse_f:
        rmse_f.write(str(sqrt(sum_squared_values / counter) if counter else 0))


def run_algorithm(algorithm, test_set, output_path, ratings_by_movie_path, ratings_by_user_path):
    os.makedirs(output_path, exist_ok=True)
    algorithm_name = algorithm.__name__
    print('Running algorithm: {0}'.format(algorithm_name))
    prefix = output_path + algorithm_name
    output_file, error_file, rmse_file = prefix + '.res.txt', prefix + '.err.txt', prefix + '.rmse.txt'
    algorithm(output_file, error_file, test_set, ratings_by_movie_path, ratings_by_user_path)
    print('Computing RMSE for algorithm: {0}'.format(algorithm_name))
    compute_rmse(output_file, rmse_file, ratings_by_user_path)


def main():
    if not os.path.exists(constants.REC_SYS_RATINGS_BY_USER):
        os.makedirs(constants.REC_SYS_RATINGS_BY_USER, exist_ok=True)
        print('Building ratings_by_user map...')
        group_netflix_ratings_by_user(constants.NETFLIX_FULL_RATINGS_DATASET_PATH, constants.REC_SYS_RATINGS_BY_USER)
        print('Map built')

    if not os.path.exists(constants.REC_SYS_RATINGS_BY_MOVIE):
        os.makedirs(constants.REC_SYS_RATINGS_BY_MOVIE, exist_ok=True)
        print('Building ratings_by_movie map...')
        group_netflix_ratings_by_movie(constants.NETFLIX_FULL_RATINGS_DATASET_PATH, constants.REC_SYS_RATINGS_BY_MOVIE)
        print('Map built')

    algorithms = [group_lens, shw, most_similar]
    test_set = load_test_set(constants.NETFLIX_TEST_SET)
    for algorithm in algorithms:
        run_algorithm(algorithm, test_set, constants.REC_SYS_OUTPUT_PATH, constants.REC_SYS_RATINGS_BY_MOVIE,
                      constants.REC_SYS_RATINGS_BY_USER)


########################################################################################################################
def main_rec():
    print('Building documents and tf-idf matrix...')
    matrix = build_tfidf_matrix(constants.OS_IDS_LIST, constants.OS_SUBS_PATH_MERGED, constants.IMDB_PLOTS_SYNOPSES)
    print('Running prediction...')
    # lotr compagnia = '120737'
    # gladiator = '172495'
    get_k_most_similar_movies('120737', matrix, 3)
    print('\n\n')
    get_k_most_similar_movies('172495', matrix, 7)


class TfidfMatrix(object):
    def __init__(self, documents, ids_list, indexes, tfidf):
        self.documents = documents
        self.ids_list = ids_list
        self.indexes = indexes
        self.tfidf = tfidf


def build_tfidf_matrix(ids_list_file, sub_folder, plots_folder):
    documents = []
    ids_list = []  # [imdb_id]
    indexes = {}  # imdb_id, doc_num
    with open(ids_list_file, 'r') as ids_list_f:
        for count, m_id in enumerate(map(lambda l: l.rstrip('\r\n'), ids_list_f)):
            documents.append(build_movie_doc(m_id, sub_folder, plots_folder))
            ids_list.append(m_id)
            indexes[m_id] = count

    tfidf = TfidfVectorizer(stop_words='english').fit_transform(documents)
    return TfidfMatrix(documents, ids_list, indexes, tfidf)


def build_movie_doc(m_id, sub_folder, plots_folder):
    with open(sub_folder + m_id + '.txt', 'r', encoding='ISO-8859-1') as script_f:
        content = script_f.read()
    if os.path.exists(plots_folder + m_id + '.txt'):
        with open(plots_folder + m_id + '.txt', 'r', encoding='ISO-8859-1') as plots_f:
            content += plots_f.read()
    return content


def get_k_most_similar_movies(m_id, rec_data, k=5):
    if m_id == '1':
        print('Crash')
    documents, ids_list, index = rec_data.documents, rec_data.ids_list, rec_data.indexes[m_id]
    cosine_similarities = linear_kernel(rec_data.tfidf[index: index + 1], rec_data.tfidf).flatten()
    # print('Unsorted similarities: {0}'.format(cosine_similarities))
    related_docs_indices = cosine_similarities.argsort()[:-(k+2):-1]
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

########################################################################################################################

if __name__ == '__main__':
    main()
