from xmlrpc.client import ServerProxy


class OpenSubtitles(object):
    ENDPOINT = 'http://api.opensubtitles.org/xml-rpc'
    DEFAULT_LANGUAGE = 'eng'
    DEFAULT_USER_AGENT = 'OSTestUserAgent'

    def __init__(self):
        self.xmlrpc = ServerProxy(OpenSubtitles.ENDPOINT, allow_none=True)
        self.token = None

    def login(self, username='', password_md5='', lang=DEFAULT_LANGUAGE, user_agent=DEFAULT_USER_AGENT):
        assert (username and password_md5) or (user_agent and user_agent is not OpenSubtitles.DEFAULT_USER_AGENT)
        data = self.xmlrpc.LogIn(username, password_md5, lang, user_agent)
        self.token = _get_from_data_on_success_or_none(data, 'token')
        return self.token

    def set_token(self, token):
        assert token
        self.token = token
        return self.token

    def logout(self):
        data = self.xmlrpc.LogOut(self.token)
        return '200' in data.get('status')

    def no_operation(self):
        data = self.xmlrpc.NoOperation(self.token)
        return '200' in data.get('status')

    def search_subtitles_for_film(self, imdb_id, language):
        data = self.xmlrpc.SearchSubtitles(self.token, [{'imdbid': imdb_id, 'sublanguageid': language}])
        return _get_from_data_on_success_or_none(data, 'data')

    def download_subtitles(self, subs_ids):
        data = self.xmlrpc.DownloadSubtitles(self.token, subs_ids)
        return _get_from_data_on_success_or_none(data, 'data')

    def get_imdb_movie_details(self, imdb_id):
        data = self.xmlrpc.GetIMDBMovieDetails(self.token, imdb_id)
        return _get_from_data_on_success_or_none(data, 'data')


def _get_from_data_on_success_or_none(data, key):
    status = data.get('status').split()[0]
    return data.get(key) if '200' == status else None
