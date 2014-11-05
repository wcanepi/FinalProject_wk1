"""
TBD get the poster url and provide an api to retrieve the poster
    get links to videos, screen-snaps
    get recommendations
    get user reviews
"""

from xgoogle.search import GoogleSearch, SearchError
from BeautifulSoup import BeautifulSoup
import sys, os
from urllib import FancyURLopener
from HTMLParser import HTMLParser
import re


class myURLOpener(FancyURLopener):
    version = 'Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.8) Gecko/20051111 Firefox/1.5 BAVM/1.0.0'


class pIMDB():
    def __init__(self, moviename):
        self.textblk_rexps = {
            r'directors?\s*:': 'Director(s)', 
            r'writers?\s*:': 'Writer(s)',
            r'stars?\s*:': 'Star(s)',
            r'taglines?\s*:': 'Tagline(s)',
            r'parents\s+guide\s*:': 'Parental Guide',
            r'official\s+sites\s*:': 'Official Sites',
            r'country\s*:': 'Country',
            r'language\s*:': 'Language',
            r'also\s+known\s+as\s*:': 'Title Alias',
            r'filming\s+locations\s*:': 'Filmed at',
            r'budget\s*:': 'Budget',
            r'opening\s+weekend\s*:': 'Opening Weekend Earnings',
            r'gross\s*:': 'Gross Earnings',
            r'production\s+co\s*:': 'Production Companies',
            r'runtime\s*:': 'Movie Duration',
            r'sound\s+mix\s*:': 'Sound Tech. Used',
            r'color\s*:': 'Color',
            r'aspect\s+ratio\s*:': 'Aspect-Ratio',
        }
        self.movie = moviename
        self.query = 'imdb+' + re.sub(r'\s+', '+', moviename)
        self.imdb_link = None
        self.details = None
        self.imdb_page_source = ''
        self.rating = self.outof = ''
        self.storyline = ''
        self.posterurl = ''
        # find a imdb link
        googler = GoogleSearch(self.query)
        googler.results_per_page = 10
        search_results = googler.get_results()
        for res in search_results:
            il = res.url.encode("utf8")
            if il.startswith('http://www.imdb.com'):
                self.imdb_link = il
                break
        if self.imdb_link is None:
            print "Could not get any results from IMDB for %s" % self.movie
            sys.exit(1)

    def __remove_tags(self, data):
        while re.search(r'<.+?>', data):
            data = re.sub(r'<.+?>', '', data, re.S)
        return data

    def parse_imdb_page(self):
        myopener = myURLOpener()
        htmlparser = HTMLParser()
        sock = myopener.open(self.imdb_link)
        self.imdb_page_source = sock.read()
        soup = BeautifulSoup(self.imdb_page_source)
        sock.close()
        # get rating
        #rating_ls = soup.findAll('span', attrs={'class': 'rating-rating'})
        rating_given_ls = soup.findAll('span', attrs={'itemprop': 'ratingValue'})
        best_rating_ls = soup.findAll('span', attrs={'itemprop': 'bestRating'})
        (self.rating) = re.findall(r'([\d\.]+)', str(rating_given_ls))[0]
        (self.outof) = re.findall(r'([\d\.]+)', str(best_rating_ls))[0]
        # get director, writers, earnings and other parameters
        text_blk_ls = map(lambda x: str(x), \
                            soup.findAll('div', attrs={'class': 'txt-block'}))
        text_blk = self.__remove_tags(' '.join(text_blk_ls))
        text_blk = text_blk.replace('\n', '')
        text_blk = htmlparser.unescape(text_blk)
        text_blk = text_blk.replace('\n', '')
        text_blk = re.sub(r'&[a-z]+?;', ' ', text_blk)
        text_blk = text_blk.strip()
        for textblk_rexp in self.textblk_rexps.keys():
            reobj = re.compile(textblk_rexp, re.I)
            text_blk = reobj.sub('\n%s >>> ' % \
                self.textblk_rexps[textblk_rexp], text_blk)
        text_blk = re.sub(r' +', ' ', text_blk, re.S)
        self.details = map(lambda x: x.strip(), text_blk.split('\n'))
        self.details = map(lambda x: re.sub(r'Official Sites.+', '', x), self.details)
        self.details = filter(lambda x: x.__ne__(''), self.details)
        self.details[-1] = re.split(r'[a-zA-Z]+\s*:', self.details[-1])[0]
        self.details[-1] = re.split(r'\s+[Tt]rivia', self.details[-1])[0]
        seemore_re = re.compile(r'see\s*(more|all).+', re.S|re.I)
        self.details = map(lambda x: seemore_re.sub('', x), self.details)
        # get a story-line
        storyline_regex = re.compile(r'<em\s+class=.nobr.>\s*Written\s+by.+', re.I | re.S)
        self.storyline = filter(lambda x: storyline_regex.search(str(x)), soup.findAll('p'))[0]
        self.storyline = storyline_regex.sub('', str(self.storyline))
        self.storyline = htmlparser.unescape(self.__remove_tags(self.storyline))
        # get poster url self.posterurl
        try:
            self.posterurl = re.search(r'src=.(.+?)[\'"]', str(soup.findAll('img', \
                title=re.compile(r'.+?poster\s*', re.I))[0])).group(1)
        except IndexError:
            print "Could not get the poster url"
            self.posterurl = ''
            pass

    def download_poster(self, dest):
        # code to retrieve the poster image from self.posterurl
        if self.posterurl != '':
            myopener.retrieve(self.posterurl, dest)
        return

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print "Usage: %s <movie name>" % sys.argv[0]
        sys.exit(1)
    movie = re.sub(r'[^a-zA-Z0-9\']+', ' ', sys.argv[1])
    imdb = pIMDB(movie)
    imdb.parse_imdb_page()
    print "imdb link:\n\t", imdb.imdb_link
    print "\nmovie name:\n\t", imdb.movie
    print "\nmovie rating:\n\t%s/%s" % (imdb.rating, imdb.outof)
    print "\nmovie details:\n\t%s" % '\n\t'.join(imdb.details)
    print "\nmovie storyline:\n\t%s" % imdb.storyline
