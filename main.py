# coding: windows-1251
import sys

from film import Film, Feed
from rutracker import RuTrackerAgent, AlreadyDownloaded
from automatic_torrent_start import run_qbittorrent
import feedparser
import db_updater as db
import json_db as jdb

import logging

logging.basicConfig(level=logging.INFO)
logging.basicConfig(format=u'%(filename)s[LINE:%(lineno)d]# %(levelname)-8s [%(asctime)s]  %(message)s',
                    level=logging.INFO)

db_filename = 'film_base.json'


def already_downloaded(film_description):
    dbx = db.set_up_dropbox()
    try:
        film_base = jdb.read_from_db(dbx, db_filename)
        if film_description in film_base['records']:
            return True
        else:
            return False
    except EnvironmentError:
        logging.warning('%s doesn\'t exists!' % db_filename)
        logging.error("Unexpected error!", exc_info=sys.exc_info())
        jdb.new_empty_db(dbx, db_filename)
        return False


if __name__ == '__main__':
    l = Feed('Latest movies', lambda title: 'BDRip'.lower() in title.lower() and \
                                            ('720p'.lower() in title.lower() in title.lower()),
             lambda film: (film.IMDBrating >= 6.5 and film.IMDBvotes >= 10000) or (film.IMDBrating >= 8.0),
             lambda film: film.size,
             'http://feed.rutracker.org/atom/f/313.atom')
    feeds = [l]
    films = list()
    films_to_base = list()
    downloads_list = list()
    rutracker_agent = RuTrackerAgent()
    for rf in feeds:
        filmsRss = feedparser.parse(rf.url)
        logging.info('Loaded %s films from \"%s\"' % str(len(filmsRss.entries)), rf.title)
        filtered_entries = list(filter(lambda x: rf.headerFilter(x.title), filmsRss.entries))
        logging.info('Saved %s films after filtering by title' % str(len(filtered_entries)))
        films.extend(map(lambda x: Film(x), filtered_entries))
        films = list(filter(lambda x: rf.ratingFilter(x), films))
        logging.info('Saved %s films after filtering by IMDB rating' % str(len(films)))

        for film in films:
            json_film = {
                'title': film.title,
                'rus_title': film.rus_title,
                'IMDBrating': film.IMDBrating,
                'size': film.size,
                'topic': film.topicURL + film.topicId,
                'year': film.year
            }
            if not already_downloaded(json_film):
                films_to_base.append(json_film)
                downloads_list.append(rutracker_agent.download_torrent(film.title, film.topicId, True))
            else:
                raise AlreadyDownloaded(json_film['title'])
    run_qbittorrent(downloads_list)