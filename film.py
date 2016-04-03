from html.parser import HTMLParser
import json

from bs4 import BeautifulSoup
import re
import requests
import sys
from xml.dom.minidom import parseString, parse

import logging

logging.basicConfig(level=logging.INFO)
logging.basicConfig(format=u'%(filename)s[LINE:%(lineno)d]# %(levelname)-8s [%(asctime)s]  %(message)s',
                    level=logging.INFO)


class Film:
    def __init__(self, rss_entry):
        self.search_imdb_url = 'http://www.imdb.com/xml/find?json=1&nr=1&tt=on&q='
        self.title = self.parse_title(rss_entry)
        self.rus_title = self.parse_rus_title(rss_entry)
        self.year = self.parse_year(rss_entry)
        self.director = self.parse_director(rss_entry)
        self.size = self.parse_size(rss_entry)
        self.topicId = rss_entry.link[len('http://rutracker.org/forum/viewtopic.php?'):]
        self.topicURL = rss_entry.link
        self.imdb_id = self.load_imdb_id()
        self.imdb_rating, self.imdb_votes = self.load_imdb_rating()
        self.kp_id = self.load_kinopoisk_id()
        self.kp_rating, self.kp_votes = self.load_kinopoisk_rating()
        # self.rssFeed = feed

    @staticmethod
    def parse_size(rss_entry):
        match = re.search('(\[\d{1,3}.\d{1,2} GB)', rss_entry.title)
        if match:
            size = float(match.group(0)[1:-3].strip())
        else:
            size = 0
            logging.warning('Could not parse size for %s !' % rss_entry.title)
        return size

    @staticmethod
    def parse_title(rss_entry):
        match = re.search('(/ [^/]+\()', rss_entry.title)
        if match:
            title = match.group(0)[2:-1].strip()
        else:
            title = 'Parsing error'
            logging.warning('Could not parse title!')
        return title

    def parse_rus_title(self, rss_entry):
        match = re.search('^[^/]+ /', rss_entry.title)
        if match:
            rus_title = match.group(0)[:-1].strip()
        else:
            rus_title = self.title
            logging.warning('Could not parse local title for %s!' % rss_entry.title)
        return rus_title

    @staticmethod
    def parse_year(rss_entry):
        match = re.search('(\[\d\d\d\d[\, ])', rss_entry.title)
        if match:
            year = match.group(0)[1:5].strip()
        else:
            year = 1812
            logging.warning('Could not parse year for %s!' % rss_entry.title)
        return year

    def parse_director(self, rss_entry):
        match = re.search('(/ [^/\)]+\))', rss_entry.title)
        if match:
            director = match.group(0)[2:-1].strip()
        else:
            director = 'Ronald Reygan'
            logging.warning('Could not parse director for %s!' % rss_entry.title)
        return director

    def __str__(self):
        result = list(map(lambda x: x + "=" + self.__dict__.get(x), self.__dict__.keys()))
        result.sort()

        return result.__str__()

    def load_imdb_id(self):
        imdb_request = requests.get('http://www.imdb.com/xml/find?json=1&nr=1&tt=on&q=' + self.title)
        imdb_details = json.loads(imdb_request.content)
        description_array = []

        if 'title_exact' in imdb_details:
            description_array.extend(imdb_details.get('title_exact'))
        if 'title_popular' in imdb_details:
            description_array.extend(imdb_details.get('title_popular'))

        if len(description_array):
            description_array = list(
                filter(
                    lambda x: x.get('title_description').startsWith(self.year)
                              and x.get('title_description').lower().find(self.director.lower()),
                    description_array
                )
            )

        if not len(description_array):
            logging.info('NO MATCHES FOR %s' % self.title)
            imdb_id = ''
            return imdb_id

        try:
            imdb_id = description_array[0].get('id')
            return imdb_id
        except Exception as err:

            logging.error(self, exc_info=err)
            logging.error(imdb_details)
            logging.error(description_array)

    def load_imdb_rating(self):
        imdb_votes = 0
        imdb_rating = 0.0
        try:
            omdb_request = requests.get('http://www.omdbapi.com/?i=' + self.imdb_id)
            omdb_retails = json.loads(omdb_request.content)
            try:
                imdb_votes = int(filter(lambda x: x.isdigit(), omdb_retails.get('imdbVotes')))
            except ValueError:
                logging.info("OMDB VOTES " + omdb_retails.get('imdbVotes') + " for " + self.__str__())
                imdb_votes = 0
            try:
                imdb_rating = float(omdb_retails.get('imdbRating'))
            except ValueError as err:
                logging.info("OMDB RATING " + omdb_retails.get('imdbRating') + " for " + self.__str__())
                logging.error("Unexpected error: %s" % err.__str__(), exc_info=sys.exc_info())
                imdb_rating = 0.0
        except Exception as err:
            imdb_rating = 0.0
            imdb_votes = 0
            logging.error("Unexpected error: %s" % err.__str__(), exc_info=sys.exc_info())

        return imdb_rating, imdb_votes

    def load_kinopoisk_id(self):
        kp_search_url = 'http://www.kinopoisk.ru/s/type/film/find/'

        def __set_user_agent__():
            return {'User-Agent': ' Mozilla/5.0 (Windows NT 6.1; WOW64; rv:12.0) Gecko/20100101 Firefox/12.0'}

        logger = logging.getLogger('kinobot')
        h = logging.StreamHandler(sys.stdout)
        h.setLevel(logging.DEBUG)
        logger.addHandler(h)
        try:
            page = requests.get(
                kp_search_url + self.title + '/',
                headers=__set_user_agent__())

            match = re.search('film\/(\d)+\/$', page.url)
            if match:  # we have found ID of the film already
                return match.group(0)[5:-1]

            class KP_HTMLParser(HTMLParser):
                def __init__(self):
                    HTMLParser.__init__(self)
                    self.found = None
                    self.filmid = None

                def handle_starttag(self, tag, attrs):
                    if (not self.found) and tag == 'div':
                        for a in attrs:
                            if a[1] == 'element most_wanted':
                                self.found = True
                    if self.found and tag == 'a':
                        for a in attrs:
                            if a[0] == 'href':
                                m = re.search('\/film\/(\d)+\/', a[1])
                                if m:
                                    self.filmid = m.group(0)[6:-1]
                                    self.found = False

            parser = KP_HTMLParser()
            parser.feed(page.content.decode('windows-1251'))
            if not parser.filmid:
                logging.getLogger('kinobot').warn(
                    'NO MATCHES FOR ' + self.title + " ON KINOPOISK")
                return None
            return parser.filmid
        except BaseException as e:
            logging.getLogger('kinobot').warn(
                'NO MATCHES FOR ' + self.title + " ON KINOPOISK", exc_info=e)
            return None

    def load_kinopoisk_rating(self):
        kp_votes = 0
        kp_rating = 0.0
        rating_url = 'http://www.kinopoisk.ru/rating/'

        def __set_user_agent__():
            return {'User-Agent': ' Mozilla/5.0 (Windows NT 6.1; WOW64; rv:12.0) Gecko/20100101 Firefox/12.0'}

        if not self.kp_id:
            return 0.0, 0
        try:
            page = requests.get(rating_url + self.kp_id + '.xml',
                                headers=__set_user_agent__())
            result = parseString(page.content)
            if len(result.getElementsByTagName('kp_rating')) > 0:
                kp_rating = float(result.getElementsByTagName('kp_rating')[0].childNodes[0].data)
                kp_votes = int(result.getElementsByTagName('kp_rating')[0].getAttribute('num_vote'))
        except BaseException as e:
            logging.getLogger('kinobot').warn(
                'NO MATCHES FOR ' + self.kp_id, exc_info=e)
        return kp_rating, kp_votes


class Feed:
    def __init__(self, title, header_filter, rating_filter, size_filter, url):
        self.title = title
        self.ratingFilter = rating_filter
        self.url = url
        self.headerFilter = header_filter
        self.sizeFilter = size_filter
        logging.debug('Initialized: ' + self.__str__())

    def __str__(self):
        return self.title.__str__()


def get_kinopoisk_top_list():
    top_url = 'http://www.kinopoisk.ru/top'

    def __set_user_agent__():
        return {'User-Agent': ' Mozilla/5.0 (Windows NT 6.1; WOW64; rv:12.0) Gecko/20100101 Firefox/12.0'}

    def parse_page(page):
        soup = BeautifulSoup(page.text)
        films_info = soup.find_all('a')[72:]
        a_len = len(films_info)
        films_info = [films_info[i + 1:i + 3][0] for i in range(0, a_len, 3)][:250]
        film_ids, film_titles = list(), list()
        for tags in films_info:
            film_titles.append(tags.get_text()[:-7])
            film_ids.append(tags.get('href')[6:-1])
        return film_ids, film_titles

    logger = logging.getLogger('kinobot')
    h = logging.StreamHandler(sys.stdout)
    h.setLevel(logging.INFO)
    logger.addHandler(h)
    try:
        page = requests.get(top_url, headers=__set_user_agent__())
        return parse_page(page)

    except BaseException as err:
        logging.getLogger('kinobot').warn(
            'Could not get Kinopoisk top 250 ', exc_info=err)


if __name__ == '__main__':
    # get_kinopoisk_top_list()
    f = Film()
