import re
import glob
import time

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import linear_kernel


#  http://stackoverflow.com/questions/12118720/python-tf-idf-cosine-to-find-document-similarity
#  http://scikit-learn.org/stable/modules/generated/sklearn.feature_extraction.text.TfidfVectorizer.html#sklearn.feature_extraction.text.TfidfVectorizer.get_feature_names
#  http://blog.christianperone.com/2013/09/machine-learning-cosine-similarity-for-vector-space-models-part-iii/



# os_client = OpenSubtitles()
# user_agent = 'ScriBa v1.0'
# imdb_ids = ['172495', '113497', '468569']
# imdb_ids = ['0119448', '0276981', '0120126', '0182668', '0399877', '0101591']
#
# imdb_url = 'http://www.imdb.com/title/tt0172495'
# token = 'hvmr5f1g99engqihncqo6lb665'
# token = os_client.login(user_agent=user_agent)
# os_client.set_token(token)
# print('Token: {0}\n'.format(token))
#
# for i in range(len(imdb_ids)):
#     data = os_client.search_subtitles_for_movie(imdb_ids[i], 'eng')
#     print('{0}: {1} result(s)'.format(i, len(data)))
#
# data = os_client.search_subtitles_for_movies(imdb_ids, 'eng')
# for i in range(len(data)):
#     print('{0} - {1} - {2}'.format(i, data[i]['IDMovieImdb'], data[i]['IDSubtitleFile']))
#
# list of dictionaries. Each dictionary contains the IDSubtitleFile and the SubDownloadLink
# list_dict = get_subtitle_list(os_client, imdb_id)
# print(list_dict)
# id_list = [sub['IDSubtitleFile'] for sub in list_dict]
# print(id_list)
# print(pprint(os_client.download_subtitles(id_list)))
#
# get IMDb details
# data = os_client.get_imdb_movie_details(imdb_id)
# print('Movie details: {0}\n'.format(data))
#
# search for subtitles
# data = os_client.search_subtitles_for_movie(imdb_id, 'eng')
# note that each JSON contains also the direct download link
# print('Found {0} subtitle(s):\n{1}\n[...]\n'.format(len(data), pprint(data[0])))
#
# extract all links/ids from data
# subs_links = [item['SubDownloadLink'] for item in data]
# print('Links: {0}\n'.format(subs_links))
# subs_ids = [item['IDSubtitle'] for item in data]
# print('Ids: {0}\n'.format(subs_ids))
#
# retrieve encoded gzipped data from subtitle(s) id(s)
# data = os_client.download_subtitles(subs_ids[:5])  # get data only for the first 5 subs
# print('Sub data: {0}'.format(pprint(data)))
#
# download subtitle file from encoded gzipped data
# download_sub_from_encoded_data(data[0]['data'], 'decoded_sub.srt')
#
# download subtitle file from url
# download_file_from_url(subs_links[0], 'direct_downloaded.gz')
#
# os_client.logout()
#
# extract plots and synopsis from IMDb
# plot_summaries_text, synopsis_text = get_movie_info(imdb_id)
# print('Found {0} plot(s):\n'.format(len(plot_summaries_text)))
# for i in range(0, len(plot_summaries_text)):
#     print('[{0}]: {1}'.format(i + 1, plot_summaries_text[i]))
# print('\nSynopsis: {0}'.format(synopsis_text))
#




# documents = [
#     "The sky is blue",
#     "The sun is bright",
#     "The sun in the sky is bright",
#     "We can see the shining sun, the bright sun"]
#
# tfidf_vectorizer = TfidfVectorizer(stop_words='english')
# tfidf = tfidf_vectorizer.fit_transform(documents)
#
# print('Features:\n{0}'.format(tfidf_vectorizer.get_feature_names()))
#
# cosine_similarities = linear_kernel(tfidf[0:1], tfidf).flatten()
#
# print('Unsorted similarities:\n{0}'.format(cosine_similarities))
# related_docs_indices = cosine_similarities.argsort()[:-5:-1]
# print('Ranking (indexes):\n{0}'.format(related_docs_indices))
# print('Sorted similarities:\n{0}'.format(cosine_similarities[related_docs_indices]))
# print('Most similar:\n{0}'.format(documents[related_docs_indices[1]]))


start_time = time.clock()

documents = []
indexes = {}  # imdb_id, doc_num
ids_list = []  # [imdb_id]

doc_num = 0
for ps_file in glob.glob('data/imdb/plots-synopses/*.txt'):
    with open(ps_file, 'r') as f:
        imdb_id = re.split('/|\.', ps_file)[-2]
        indexes[imdb_id] = doc_num
        content = f.read()
        documents.append(content)
        ids_list.append(imdb_id)
    doc_num += 1

print('{0}\n\ndocs num: {1}'.format(indexes, len(documents)))

tfidf_vectorizer = TfidfVectorizer(stop_words='english')
tfidf_matrix = tfidf_vectorizer.fit_transform(documents)

zorro_id = indexes.get('120746')
print(zorro_id)

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

end_time = time.clock() - start_time
print('Execution time: {0} seconds.'.format(end_time))
