from HTMLParser import HTMLParser
import json
import logging
import re
import requests
import sys
from xml.dom.minidom import parseString, parse


class Film:
    # def __init__(self, rss_entry,feed):
    def __init__(self, rss_entry):
        # print rssEntry
        # parse film native title
        self.title = self.parse_title(rss_entry)
        # parse film russian title
        self.rus_title = self.parse_rus_title(rss_entry)
        # parse film year release
        self.year = self.parse_year(rss_entry)
        # parse film director
        self.director = self.parse_director(rss_entry)
        self.size = self.parse_size(rss_entry)
        self.topicId = rss_entry.link[len('http://rutracker.org/forum/viewtopic.php?'):]
        self.topicURL = rss_entry.link
        self.KPid = self.loadKPid()
        self.IMDBid = self.loadIMDBid()
        self.IMDBrating, self.IMDBvotes = self.loadIMDBRating()
        self.KPrating, self.KPvotes = self.loadKPRating()
        # self.rssFeed = feed

    def parse_size(self, rss_entry):
        match = re.search('(\[\d{1,3}.\d{1,2} GB)', rss_entry.title)
        if match:
            size = float(match.group(0)[1:-3].strip())
        else:
            size = 0
            print 'Could not parse size!'
            print rss_entry.title
        return size

    def parse_title(self, rss_entry):
        match = re.search('(/ [^/]+\()', rss_entry.title)
        if match:
            title = match.group(0)[2:-1].strip()
        else:
            title = 'Parsing error'
            print 'Could not parse name!'
            print rss_entry.title
        return title

    def parse_rus_title(self, rss_entry):
        match = re.search('^[^/]+ /', rss_entry.title)
        if match:
            rus_title = match.group(0)[:-1].strip()
        else:
            rus_title = self.title
            print 'Could not parse Russian title!'
            print rss_entry.title
        return rus_title

    def parse_year(self, rss_entry):
        match = re.search('(\[\d\d\d\d[\, ])', rss_entry.title)
        if match:
            year = match.group(0)[1:5].strip()
        else:
            year = 1812
            print 'Could not parse year!!'
            print rss_entry.title
        return year

    def parse_director(self, rss_entry):
        match = re.search('(/ [^/\)]+\))', rss_entry.title)
        if match:
            director = match.group(0)[2:-1].strip()
        else:
            director = 'Ronald Reygan'
            print 'Could not parse director!!!'
            print rss_entry.title
        return director

    def __str__(self):
        result = map(lambda x: x + "=" + unicode(self.__dict__.get(x)), self.__dict__.keys())
        result.sort()

        return result.__str__()

    def loadIMDBid(self):
        imdbID = None
        imdbRequest = requests.get('http://www.imdb.com/xml/find?json=1&nr=1&tt=on&q=' + self.title)
        imdbDetails = json.loads(imdbRequest.content)
        descriptionArray = []

        if 'title_exact' in imdbDetails:
            descriptionArray.extend(imdbDetails.get('title_exact'))
        if 'title_popular' in imdbDetails:
            descriptionArray.extend(imdbDetails.get('title_popular'))

        if len(descriptionArray) > 1:
            descriptionArray = [x for x in descriptionArray if
                                x.get('title_description').startswith(self.year)]
            if len(descriptionArray) > 1:
                descriptionArray = [x for x in descriptionArray if
                                    x.get('title_description').lower().find(self.director.lower()) >= 0]

        if len(descriptionArray) == 0:
            print 'NO MATCHES FOR ' + self.__str__()
            imdbID = None
            return imdbID

        try:
            imdbID = descriptionArray[0].get('id')
            return imdbID
        except:
            print self
            print imdbDetails
            print descriptionArray

    def loadIMDBRating(self):
        IMDBvotes = 0
        IMDBrating = 0.0
        try:
            omdbRequest = requests.get("http://www.omdbapi.com/?i=" + self.IMDBid)
            omdbDetails = json.loads(omdbRequest.content)
            try:
                IMDBvotes = int(filter(lambda x: x.isdigit(), omdbDetails.get('imdbVotes')))
            except ValueError:
                print "OMDB VOTES " + omdbDetails.get('imdbVotes') + " for " + self.__str__()
                IMDBvotes = 0
            try:
                IMDBrating = float(omdbDetails.get('imdbRating'))
            except ValueError:
                print "OMDB RATING " + omdbDetails.get('imdbRating') + " for " + self.__str__()
                IMDBrating = 0.0
                # return IMDBrating, IMDBvotes
        except:
            IMDBrating = 0.0
            IMDBvotes = 0
            print "Unexpected error:", sys.exc_info()
            return IMDBrating, IMDBvotes

        return IMDBrating, IMDBvotes

    def loadKPid(self):
        def __set_user_agent__():
            return {'User-Agent': ' Mozilla/5.0 (Windows NT 6.1; WOW64; rv:12.0) Gecko/20100101 Firefox/12.0'}

        logger = logging.getLogger('kinobot')
        h = logging.StreamHandler(sys.stdout)
        h.setLevel(logging.DEBUG)
        logger.addHandler(h)
        try:
            r = requests.get(
                'http://www.kinopoisk.ru/s/type/film/find/' + self.title + '/',
                headers=__set_user_agent__())

            match = re.search('film\/(\d)+\/$', r.url)
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
            parser.feed(r.content.decode('windows-1251'))
            if not parser.filmid:
                logging.getLogger('kinobot').warn(
                    'NO MATCHES FOR ' + self.title + " ON KINOPOISK")
                return None
            return parser.filmid
        except BaseException as e:
            logging.getLogger('kinobot').warn(
                'NO MATCHES FOR ' + self.title + " ON KINOPOISK", exc_info=e)
            return None

    def loadKPRating(self):
        KPvotes = 0
        KPrating = 0.0

        def __set_user_agent__():
            return {'User-Agent': ' Mozilla/5.0 (Windows NT 6.1; WOW64; rv:12.0) Gecko/20100101 Firefox/12.0'}

        if not self.KPid:
            return 0.0, 0
        try:
            ratingR = requests.get('http://www.kinopoisk.ru/rating/' + self.KPid + '.xml',
                                   headers=__set_user_agent__())
            result = parseString(ratingR.content)
            if len(result.getElementsByTagName('kp_rating')) > 0:
                KPrating = float(result.getElementsByTagName('kp_rating')[0].childNodes[0].data)
                KPvotes = int(result.getElementsByTagName('kp_rating')[0].getAttribute('num_vote'))
        except BaseException as e:
            logging.getLogger('kinobot').warn(
                'NO MATCHES FOR ' + self.KPid, exc_info=e)
        return KPrating, KPvotes


class Feed:
    def __init__(self, title, headerFilter, ratingFilter, sizeFilter, url):
        self.title = title
        self.ratingFilter = ratingFilter
        self.url = url
        self.headerFilter = headerFilter
        self.sizeFilter = sizeFilter

    def __str__(self):
        return self.title.__str__()


def get_kpTop250_film_list():
    def __set_user_agent__():
        return {'User-Agent': ' Mozilla/5.0 (Windows NT 6.1; WOW64; rv:12.0) Gecko/20100101 Firefox/12.0'}

    class MyHTMLParser(HTMLParser):
        def __init__(self):
            MyHTMLParser.__init__(self)
            self.found = None
            self.found_local_name = None
            self.film_id_list = list()
            self.film_local_names = list()

        def handle_starttag(self, tag, attrs):
            if (not self.found) and tag == 'tr':
                for attr in attrs:
                    if str(attr[1]).startswith('top250_place_'):
                        self.found = True
            if self.found and tag == 'a':
                for attr in attrs:
                    if attr[0] == 'href':
                        m = re.search('\/film\/(\d)+\/', attr[1])
                        if m:
                            self.film_id_list.append(m.group(0)[6:-1])
                            self.found = False
                            self.found_local_name = True

        def handle_data(self, data):
            if self.found_local_name and data.strip():
                self.film_local_names.append(data)
                self.found_local_name = False

    logger = logging.getLogger('smogbot')
    h = logging.StreamHandler(sys.stdout)
    h.setLevel(logging.DEBUG)
    logger.addHandler(h)
    try:
        top_rating_films = requests.get('http://www.kinopoisk.ru/top',
                                        headers=__set_user_agent__())
        parser = MyHTMLParser()
        parser.feed(top_rating_films.content.decode('windows-1251'))
        return parser.film_id_list, parser.film_local_names

    except BaseException as err:
        logging.getLogger('smogbot').warn(
            'Could not get Kinopoisk top 250 ', exc_info=err)

