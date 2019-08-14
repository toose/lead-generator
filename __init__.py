#!/usr/bin/env python3

import os, requests, logging, argparse
from urllib import parse
from bs4 import BeautifulSoup
import re

class Lead():
    def __init__(self, name, phone, street, locale, category):
        self.name = name
        self.category = category
        self.phone = phone
        self.street = street
        self._parse_locale(locale)
    
    def _parse_locale(self, locale):
        if locale is not None:
            regex = re.compile(r'(.*),\s(\w{2})\s(\d{5})')
            match = regex.match(locale)
            self.city = match.groups()[0]
            self.state = match.groups()[1]
            self.postal = match.groups()[2]
        else:
            self.city, self.state, self.postal = '', '', ''


class WebPage():
    def __init__(self, keyword, location, uri='https://yellowpages.com'):
        self.uri = uri
        self.keyword = keyword
        self.location = location
        self.logger = logging.getLogger('scrape.webpage')

    def _get_uri(self, search= {}):
        uri = self.uri
        if search:
            uri += '/search?{}'.format(parse.urlencode(search))
            self.logger.debug(uri)
        return uri        

    def _get_response(self, keyword, location):
        search_terms = {'search_terms': keyword, 'geo_location_terms': location}
        uri = self._get_uri(search_terms)
        response = requests.get(uri)
        response.raise_for_status()
        return response

    def _get_next_page(self):
        pass

    def parse_results(self):
        results = []
        response = self._get_response(keyword=self.keyword, location=self.location)
        soup = BeautifulSoup(response.content, 'html.parser')
        results = soup.find_all(id=re.compile('^lid')) # First page results
        pagination = soup.find(class_='pagination')
        pages = pagination.find_all('a')
        #for page in pages: 




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
    
    lead_list = []
    web_page = WebPage(keyword=args.keyword, location=args.location)
    results = web_page.parse_results()
    for result in results:
        name = result.find(class_='business-name').string if result.find(
            class_='business-name') else ''
        category = ','.join([x for x in result.find(class_='categories').strings])
        phone = result.find(class_='phone').string if result.find(
            class_='phone') else ''
        street = result.find(class_='street-address').string if result.find(
            class_='street-address') else ''
        locale = result.find(class_='locality').string if result.find(
            class_='locality') else ''
        lead = Lead(name=name, phone=phone, street=street, locale=locale,
                    category=category)
        lead_list.append(lead)

    
if __name__ == '__main__':
    main()