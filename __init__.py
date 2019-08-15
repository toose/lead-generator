#!/usr/bin/env python3

import os, requests, logging, argparse
from urllib import parse
from bs4 import BeautifulSoup
import re, math, time

class Lead():
    def __init__(self, name, phone, street, locale, category):
        self.name = name
        self.category = category
        self.phone = phone
        self.street = street
        self._parse_locale(locale)
    
    def _parse_locale(self, locale):
        if locale:
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

    def _get_uri(self, search=None):
        uri = self.uri
        if search:
            uri += '/search?{}'.format(parse.urlencode(search))
            self.logger.debug(uri)
        return uri        

    def _get_response(self, keyword, location, page=None):
        search_terms = [('search_terms', keyword), ('geo_location_terms', location)]
        if page is not None:
            search_terms.append(('page', page))
        uri = self._get_uri(search_terms)
        response = requests.get(uri)
        response.raise_for_status()
        return response

    def _get_num_pages(self, parser):
        pagination = parser.find(class_='pagination')
        regex = re.search(r'(\d+)', pagination.p.text)
        num_results = int(regex.groups()[0])
        return math.ceil(num_results / 30)

    def _get_results(self, response):
        parser = BeautifulSoup(response.content, 'html5lib')
        #return parser.find_all(id=re.compile('^lid')) # First page results
        return parser.find_all(class_='result')

    def _parse_results(self, results):
        parsed_results = []
        for result in results:
            name = result.find(class_='business-name').string if result.find(
                class_='business-name') else ''
            category = ', '.join([x for x in result.find(class_='categories').strings])
            phone = result.find(class_='phone').string if result.find(
                class_='phone') else ''
            street = result.find(class_='street-address').string if result.find(
                class_='street-address') else ''
            locale = result.find(class_='locality').string if result.find(
                class_='locality') else ''
            #self.logger.debug(f'Name: {name}; Category: {category}; Phone: {phone}; ' + 
                                #f'Street: {street}; Locality: {locale}')
            self.logger.debug(f'Name: {name}; Locality: {locale}')
            parsed_results.append((name, category, phone, street, locale))
        return parsed_results
                
    def get_leads(self):
        results = []
        response = self._get_response(self.keyword, self.location)
        parser = BeautifulSoup(response.content, 'html.parser')
        num_pages = self._get_num_pages(parser)
        self.logger.info(f'{num_pages} total pages of results')
        for num in range(1, num_pages):
            response = self._get_response(self.keyword, self.location, num)
            results += self._get_results(response)
        parsed_results = self._parse_results(results)
        #self.logger.debug(parsed_results)
        return parsed_results


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
    results = web_page.get_leads()
    for result in results:
        name, category, phone, street, locale = result
        lead = Lead(name=name, phone=phone, street=street, locale=locale,
                    category=category)
        lead_list.append(lead)
    logger.info('Leads created successfully.')
    print(lead_list)

    
if __name__ == '__main__':
    main()