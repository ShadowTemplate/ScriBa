import os

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import linear_kernel

import constants


def build_movies_docs(ids_list_file, sub_folder, plots_folder):
    documents = []
    with open(ids_list_file, 'r') as ids_list_f:
        for m_id in map(lambda l: l.rstrip('\r\n'), ids_list_f):
            documents.append(build_movie_doc(m_id, sub_folder, plots_folder))
    return documents


def build_movie_doc(m_id, sub_folder, plots_folder):
    with open(sub_folder + m_id + '.txt', 'r') as script_f:
        content = script_f.read()
    if os.path.exists(plots_folder + m_id + '.txt'):
        with open(plots_folder + m_id + '.txt', 'r') as plots_f:
            content += plots_f.read()
    return content


def main():
    documents = []
    ids_list = []  # [imdb_id]
    indexes = {}  # imdb_id, doc_num
    with open(constants.OS_IDS_LIST, 'r') as ids_list_f:
        for count, m_id in enumerate(map(lambda l: l.rstrip('\r\n'), ids_list_f)):
            documents.append(build_movie_doc(m_id, constants.OS_SUBS_PATH_MERGED, constants.IMDB_PLOTS_SYNOPSES))
            ids_list.append(m_id)
            indexes[m_id] = count

    tfidf_vectorizer = TfidfVectorizer(stop_words='english')
    tfidf = tfidf_vectorizer.fit_transform(documents)
    print('Features:\n{0}'.format(tfidf_vectorizer.get_feature_names()))
    cosine_similarities = linear_kernel(tfidf[0:1], tfidf).flatten()

    print('Unsorted similarities:\n{0}'.format(cosine_similarities))
    related_docs_indices = cosine_similarities.argsort()[:-5:-1]
    print('Ranking (indexes):\n{0}'.format(related_docs_indices))
    print('Sorted similarities:\n{0}'.format(cosine_similarities[related_docs_indices]))
    most_similar_id = related_docs_indices[1]
    print('Most similar plot/syn:\n{0}\n\nId:{1}'.format(documents[most_similar_id], ids_list[most_similar_id]))

if __name__ == '__main__':
    main()

# 12349