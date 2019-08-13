import os, requests, logging, argparse
from urllib import parse
from bs4 import BeautifulSoup

class Lead(object):
    pass

class WebPage(object):
    def __init__(self, uri='https://yellowpages.com'):
        self.uri = uri
        self.logger = logging.getLogger('scrape.webpage')

    def _get_uri(self, search= {}):
        uri = self.uri
        if search:
            uri += '/search?{}'.format(parse.urlencode(search))
            self.logger.debug(uri)
        return uri

    def get(self, keyword, location):
        search_terms = {'search_terms': keyword, 'geo_location_terms': location}
        uri = self._get_uri(search_terms)
        response = requests.get(uri)
        response.raise_for_status()
        return response


def main():
    parser = argparse.ArgumentParser(description='Sales lead scraper')
    parser.add_argument('-k', '--keyword', required=True)
    parser.add_argument('-l', '--location', required=True)
    parser.add_argument('-v', '--verbose', action='count')
    args = parser.parse_args()

    if args.verbose == None:
        log_level = logging.ERROR
    elif args.verbose == 1:
        log_level = logging.WARN
    elif args.verbose == 2:
        log_level = logging.INFO
    elif args.verbose > 2:
        log_level = logging.DEBUG
    logging.basicConfig(level=log_level)
    logger = logging.getLogger('scrape.main')

    #search = {'search_terms': args.keyword, 'geo_location_terms': args.location}
    
    web_page = WebPage()
    response = web_page.get(keyword=args.keyword, location=args.location)

    
if __name__ == '__main__':
    main()