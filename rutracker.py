import base64
import cookielib
import urllib
import urllib2
import os
from environment import environment
from automatic_torrent_start import run_qbittorrent


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
        self.post_params = urllib.urlencode({
            'login_username': environment.get('rutracker_login'),
            'login_password': base64.b64decode(environment.get('rutracker_password_base64')),
            'login': '%C2%F5%EE%E4'
        })
        self.cookie = self.__set_cookies__()
        self.opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(self.cookie))
        urllib2.install_opener(self.opener)
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
            print 'Authorizing on RuTracker...'
            self.opener.open('http://login.rutracker.org/forum/login.php', self.post_params)
            print 'Authorized'
            self.authorized = True

    def download_torrent(self, name, topic_id, to_rewrite):
        filename = filter(lambda x: x.isalpha() or x.isdigit(), name)
        filename_path = environment.get('downloaded_torrents_location') + filename + '.torrent'

        if (not os.path.exists(filename_path)) or to_rewrite:
            try:
                self.__authorise__()
            except:
                raise CannotAuthorize("RuTracker.org")
            with open(filename_path, 'wb') as torrent_file:
                print 'Downloading ' + filename_path
                web_file = self.opener.open('http://dl.rutracker.org/forum/dl.php?' + topic_id, self.post_params)
                torrent_file.write(web_file.read())
                torrent_file.close()
                print 'Downloaded'
        else:
            raise AlreadyDownloaded(filename_path)
        return filename_path


if __name__ == '__main__':
    a = RuTrackerAgent()
    file_list = list()
    file_list.append(a.download_torrent("The Man from UNCLE", 't=5108226', True))
    run_qbittorrent(file_list)
