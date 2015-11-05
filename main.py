# coding: windows-1251
from film import Film, Feed
import feedparser
from environment import environment

if __name__ == '__main__':
    l = Feed('Latest movies', lambda title: 'BDRip'.lower() in title.lower() and \
                                            ('720p'.lower() in title.lower() or '1080p'.lower() in title.lower()),
             lambda film: (film.IMDBrating >= 6.5 and film.IMDBvotes >= 10000) or (film.IMDBrating >= 8.0),
             lambda film: film.size,
             'http://feed.rutracker.org/atom/f/313.atom')
    feeds = [l]
    films = []
    for rf in feeds:
        filmsRss = feedparser.parse(rf.url)
        print 'Loaded ' + str(len(filmsRss.entries)) + ' films from "' + rf.title + '"'
        filteredEntries = filter(lambda x: rf.headerFilter(x.title), filmsRss.entries)
        print 'Saved ' + str(len(filteredEntries)) + ' after filtering by title'
        films.extend(map(lambda x: Film(x, rf), filteredEntries))
        films = filter(lambda x: rf.ratingFilter(x), films)
        print 'Saved ' + str(len(films)) + ' after filtering by IMDB rating'
        for film in films:
            print "  %s" % film.title, film.size
