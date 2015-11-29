from xmlrpc.client import ServerProxy


def _get_from_data_on_success_or_none(data, key):
    status = data.get('status').split()[0]
    return data.get(key) if '200' == status else None


class OpenSubtitles(object):
    ENDPOINT = 'http://api.opensubtitles.org/xml-rpc'

    def __init__(self):
        self.xmlrpc = ServerProxy(OpenSubtitles.ENDPOINT, allow_none=True)
        self.token = None

    def login(self, user_agent):
        assert user_agent is not None
        data = self.xmlrpc.LogIn(user_agent)
        self.token = _get_from_data_on_success_or_none(data, 'token')
        return self.token

    def logout(self):
        data = self.xmlrpc.LogOut(self.token)
        return '200' in data.get('status')

    def search_subtitles(self, params):
        data = self.xmlrpc.SearchSubtitles(self.token, params)
        return _get_from_data_on_success_or_none(data, 'data')

    def no_operation(self):
        '''Return True if the session is actived, False othercase.

        .. note:: this method should be called 15 minutes after last request to
                  the xmlrpc server.
        '''
        data = self.xmlrpc.NoOperation(self.token)
        return '200' in data.get('status')

    def download_subtitles(self):
        # array DownloadSubtitles( $token, array($IDSubtitleFile, $IDSubtitleFile,...) )
        raise NotImplementedError

    def get_imdb_movie_details(self):
        # array GetIMDBMovieDetails( $token, $imdbid )
        raise NotImplementedError
