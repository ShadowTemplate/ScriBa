from opensubtitles import OpenSubtitles
from imdb import *

os_client = OpenSubtitles()
user_agent = 'ScriBa v1.0'
imdb_id = '172495'
# imdb_url = 'http://www.imdb.com/title/tt0172495'
token = '3eafo1ijeob0bh8cou2f8s36p1'
# token = os_client.login(user_agent=user_agent)
os_client.set_token(token)
print('Token: {0}\n'.format(token))

# get IMDb details
data = os_client.get_imdb_movie_details(imdb_id)
print('Movie details: {0}\n'.format(data))

# search for subtitles
# data = os_client.search_subtitles_for_film(imdb_id, 'eng')
# note that each JSON contains also the direct download link
# print('Found {0} subtitle(s):\n{1}\n[...]\n'.format(len(data), pretty_format(data[0])))

# extract all links/ids from data
# subs_links = [item['SubDownloadLink'] for item in data]
# print('Links: {0}\n'.format(subs_links))
# subs_ids = [item['IDSubtitle'] for item in data]
# print('Ids: {0}\n'.format(subs_ids))

# retrieve encoded gzipped data from subtitle(s) id(s)
# data = os_client.download_subtitles(subs_ids[:5])  # get data only for the first 5 subs
# print('Sub data: {0}'.format(pretty_format(data)))

# download subtitle file from encoded gzipped data
# serialize_sub(data[0]['data'], 'decoded_sub.srt')

# download subtitle file from url
# download_file_from_url(subs_links[0], 'direct_downloaded.gz')

# os_client.logout()

# extract plots and synopsis from IMDb
plot_summaries_text, synopsis_text = get_movie_info(imdb_id)
print('Found {0} plot(s):\n'.format(len(plot_summaries_text)))
for i in range(0, len(plot_summaries_text)):
    print('[{0}]: {1}'.format(i + 1, plot_summaries_text[i]))
print('\nSynopsis: {0}'.format(synopsis_text))
