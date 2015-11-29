import requests
from bs4 import BeautifulSoup


def get_movie_info(imdb_id):
    imdb_home_url = 'http://imdb.com'
    movie_url = imdb_home_url + '/title/tt' + imdb_id
    req = requests.get(movie_url)
    if req.status_code != 200:
        raise RuntimeError('Invalid request to URL: ', movie_url)

    soup = BeautifulSoup(req.text, 'html.parser')
    plot_summaries = soup.find(lambda tag: tag.text == 'Plot Summary')
    plot_summaries_text = get_plots(imdb_home_url + plot_summaries['href']) if plot_summaries else ''
    synopsis = soup.find(lambda tag: tag.text == 'Plot Synopsis')
    synopsis_text = get_synopsis(imdb_home_url + synopsis['href']) if synopsis else ''
    return plot_summaries_text, synopsis_text


def get_plots(plot_url):
    req = requests.get(plot_url)
    if req.status_code != 200:
        raise RuntimeError('Invalid request to URL: ', plot_url)

    soup = BeautifulSoup(req.text, 'html.parser')
    plot_summaries_tags = soup.find_all('p', class_='plotSummary')
    return [plot_tag.text.strip() for plot_tag in plot_summaries_tags]


def get_synopsis(synopsis_url):
    req = requests.get(synopsis_url)
    if req.status_code != 200:
        raise RuntimeError('Invalid request to URL: ', synopsis_url)

    soup = BeautifulSoup(req.content, 'html5lib')
    text_tags = soup.find('div', id='swiki.2.1').find_all(text=True)
    return '\n'.join([tag for tag in text_tags])