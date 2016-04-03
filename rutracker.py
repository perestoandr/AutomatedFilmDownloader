import base64
import http.cookiejar as cookielib
import urllib.request as request
import urllib.parse as urlparse
import os
from environment import environment
from automatic_torrent_start import run_qbittorrent
import logging

logging.basicConfig(level=logging.INFO)
logging.basicConfig(format=u'%(filename)s[LINE:%(lineno)d]# %(levelname)-8s [%(asctime)s]  %(message)s',
                    level=logging.INFO)


class AlreadyDownloaded(Exception):
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return str(self.value)


class CannotAuthorize(Exception):
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return str(self.value)


class RuTrackerAgent:
    def __init__(self):
        self.post_params = urlparse.urlencode({
            'login_username': environment.get('rutracker_login'),
            'login_password': base64.b64decode(environment.get('rutracker_password_base64')),
            'login': '%C2%F5%EE%E4'
        })
        self.cookie = self.__set_cookies__()
        self.opener = request.build_opener(request.HTTPCookieProcessor(self.cookie))
        request.install_opener(self.opener)
        self.authorized = False

    @staticmethod
    def __set_cookies__():
        cookie = cookielib.CookieJar()
        cookie.clear_expired_cookies()
        cookie.clear_session_cookies()
        return cookie

    def __del__(self):
        self.cookie.clear_expired_cookies()
        self.cookie.clear_session_cookies()

    def __authorise__(self):
        if not self.authorized:
            logging.info('Authorizing on RuTracker...')
            self.opener.open(environment['rutracker_login_url'], self.post_params)
            logging.info('Authorized')
            logging.info('Authorized')
            self.authorized = True

    def download_torrent(self, name, topic_id, to_rewrite):
        filename = filter(lambda x: x.isalpha() or x.isdigit(), name)
        filename_path = environment.get('downloaded_torrents_location') + filename + '.torrent'
        logging.debug('Downloading as: ' + filename_path)

        if (not os.path.exists(filename_path)) or to_rewrite:
            try:
                self.__authorise__()
            except:
                raise CannotAuthorize("RuTracker.org")
            with open(filename_path, 'wb') as torrent_file:
                print
                'Downloading ' + filename_path
                web_file = self.opener.open('http://dl.rutracker.org/forum/dl.php?' + topic_id, self.post_params)
                torrent_file.write(web_file.read())
                torrent_file.close()
                print
                'Downloaded'
        else:
            logging.info('File ' + filename_path + ' already exists')
            raise AlreadyDownloaded(filename_path)
        logging.info('Downloaded as: ' + filename_path)
        return filename_path


if __name__ == '__main__':
    a = RuTrackerAgent()
    file_list = list()
    file_list.append(a.download_torrent("The Man from UNCLE", 't=5108226', True))
    run_qbittorrent(file_list)
