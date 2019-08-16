#!/usr/bin/env python3

import re, math, time, csv, os, requests, logging, argparse
from urllib import parse
from bs4 import BeautifulSoup


class WebPage():
    def __init__(self, keyword, location, uri='https://yellowpages.com'):
        self.uri = uri
        self.keyword = keyword
        self.location = location
        self.session = requests.Session()
        self.session.headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.95 Safari/537.36'}
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
        response = self.session.get(uri)
        response.raise_for_status()
        return response

    def _get_num_pages(self, parser):
        pagination = parser.find(class_='pagination')
        regex = re.search(r'(\d+)', pagination.p.text)
        num_results = int(regex.groups()[0])
        return math.ceil(num_results / 30)

    def _get_results(self, response):
        results = []
        parser = BeautifulSoup(response.text, 'html5lib')
        for result in parser.select('.search-results .result'):
            name = result.select_one('.business-name')
            category = result.select_one('.categories')
            phone = result.select_one('.phones')
            street = result.select_one('.street-address')
            locale = result.select_one('.locality')
            website = result.select_one('.track-visit-website')

            link = parse.urljoin(self.uri, name['href']) if name else ''
            name = name.get_text(strip=True, separator=" ") if name else ''
            category = category.get_text(strip=True, separator=", ") if category else ''
            phone = phone.get_text(strip=True, separator=" ") if phone else ''
            street = street.get_text(strip=True, separator=" ") if street else ''
            locale = locale.get_text(strip=True, separator=" ") if locale else ''
            website = website['href'] if website else ''
            self.logger.debug(f'Name: {name}; Category: {category}; Phone: {phone}; ' + 
                f'Street: {street}; Locality: {locale}; Website: {website}; Link: {link}')
            results.append({'BusinessName': name, 'Category': category, 'Phone': phone,
                            'Street': street, 'Locale': locale, 'Website': website, 'Link': link})
        return results
                
    def get_leads(self):
        results = []
        response = self._get_response(self.keyword, self.location)
        parser = BeautifulSoup(response.text, 'html5lib')
        num_pages = self._get_num_pages(parser)
        self.logger.info(f'{num_pages} total pages of results')
        for num in range(1, num_pages):
            response = self._get_response(self.keyword, self.location, num)
            time.sleep(1)
            results += self._get_results(response)
        #self.logger.debug(parsed_results)
        return results


def main():
    parser = argparse.ArgumentParser(description='Sales lead scraper')
    parser.add_argument('-k', '--keyword', required=True)
    parser.add_argument('-l', '--location', required=True)
    parser.add_argument('-o', '--output-file', required=True)
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
    with open(args.output_file, 'w', newline='') as csvfile:
        fieldnames = ['BusinessName', 'Category', 'Phone', 'Street', 'City', 'State', 'Zip', 'Website', 'Link']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for result in results:
            regex = re.compile(r'(.*),\s(\w{2})\s(\d{5})')
            match = regex.match(result['Locale'])
            result['City'] = match.groups()[0] if match else ''
            result['State'] = match.groups()[1] if match else ''
            result['Zip'] = match.groups()[2] if match else ''
            del result['Locale']
            writer.writerow(result)

    logger.info(f'Lead file created successfully: {args.output_file}')

    
if __name__ == '__main__':
    main()