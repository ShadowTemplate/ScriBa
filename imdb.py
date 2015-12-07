import os

import requests
from bs4 import BeautifulSoup

import constants
import utils


def get_movie_info(imdb_id):
    movie_url = constants.IMDB_HOME_URL + '/title/tt' + imdb_id
    req = requests.get(movie_url)
    if req.status_code != 200:
        raise RuntimeError('Invalid request to URL: ', movie_url)
    soup = BeautifulSoup(req.text, 'html.parser')
    plot_summaries = soup.find(lambda tag: tag.text == 'Plot Summary')
    plot_summaries_text = get_plots(constants.IMDB_HOME_URL + plot_summaries['href']) if plot_summaries else ''
    synopsis = soup.find(lambda tag: tag.text == 'Plot Synopsis')
    synopsis_text = get_synopsis(constants.IMDB_HOME_URL + synopsis['href']) if synopsis else ''
    return plot_summaries_text, synopsis_text


def get_plots(plot_url):
    req = requests.get(plot_url)
    if req.status_code != 200:
        raise RuntimeError('Invalid request to URL: ', plot_url)
    plot_summaries_tags = BeautifulSoup(req.text, 'html.parser').find_all('p', class_='plotSummary')
    return list(map(lambda plot_tag: plot_tag.text.strip(), plot_summaries_tags))


def get_synopsis(synopsis_url):
    req = requests.get(synopsis_url)
    if req.status_code != 200:
        raise RuntimeError('Invalid request to URL: ', synopsis_url)
    return '\n'.join(BeautifulSoup(req.content, 'html5lib').find('div', id='swiki.2.1').find_all(text=True))


def extract_imdb_data_from_ids(ids_file, data_folder, lines_to_skip=0):
    os.makedirs(data_folder, exist_ok=True)
    with open(ids_file, 'r') as f:
        for movie_id in map(lambda l: l.rstrip('\r\n'), utils.iterate_after_dropping(f, lines_to_skip)):
            lines_to_skip += 1
            print('Processing movie {0} at line {1}...'.format(movie_id, lines_to_skip))
            plot_summaries_text, synopsis_text = get_movie_info(movie_id)
            print('Found: {0} plot(s), {1} synopsis/es'.format(len(plot_summaries_text), int(bool(synopsis_text))))
            with open(data_folder + movie_id + '.txt', 'w') as meta_f:
                meta_f.write('\n'.join(plot_summaries_text + [synopsis_text]))
    print('Plots/synopses extraction completed.')


def main():
    extract_imdb_data_from_ids(constants.OS_IDS_LIST, constants.IMDB_PLOTS_SYNOPSES)


if __name__ == '__main__':
    main()
