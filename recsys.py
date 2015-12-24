import os

import klepto
from bidict import bidict
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import linear_kernel

import constants


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


def get_similar_movies(m_id, rec_data):
    documents, ids_list, index = rec_data.documents, rec_data.ids_list, rec_data.indexes[m_id]
    cosine_similarities = linear_kernel(rec_data.tfidf[index: index + 1], rec_data.tfidf).flatten()
    print('Unsorted similarities:\n{0}'.format(cosine_similarities))
    related_docs_indices = cosine_similarities.argsort()[:-7:-1]
    print('Ranking (indexes):\n{0}'.format(related_docs_indices))
    print('Sorted similarities:\n{0}'.format(cosine_similarities[related_docs_indices]))
    print('\nMost similar plot/syn:')
    for i in range(len(related_docs_indices) - 1):
        similar_id = related_docs_indices[i + 1]
        print('{0} - IMDb id: {1} - Plot: {2}'.format(i + 1, ids_list[similar_id], documents[similar_id]))


def main():
    if not os.path.exists(constants.REC_SYS_PATH):
        print('Building documents and tf-idf matrix...')
        matrix = build_tfidf_matrix(constants.OS_IDS_LIST, constants.OS_SUBS_PATH_MERGED, constants.IMDB_PLOTS_SYNOPSES)
        os.makedirs(constants.REC_SYS_PATH)
        print('Storing data on file...')
        k = klepto.archives.file_archive(constants.REC_SYS_PATH + 'matrix.dat')
        k['matrix'] = matrix
        k.dump()  # pickle.dump(matrix, )
    else:
        print('Loading data from file...')
        k = klepto.archives.file_archive(constants.REC_SYS_PATH + 'matrix.dat')
        k.load()
        matrix = k['matrix']

    print('Running prediction...')
    # lotr compagnia = '120737'
    # gladiator = '172495'
    get_similar_movies('120915', matrix)


if __name__ == '__main__':
    # a = bidict()     a['k'] = 'v'     print(a.inv['v'])
    main()

# 12349
