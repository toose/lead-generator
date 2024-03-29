#!/usr/bin/env python3

import re, math, time, csv, os, requests, logging, argparse, threading
from urllib import parse
from bs4 import BeautifulSoup


class WebPage():
    """Webpage scraper class.

    Scrapes yellowpages.com for business information based on a 
    keyword and location.

    Attributes:
        uri: The uri/url to scrape (default: https://yellowpages.com)
        keyword: Search terms against yellowpages.com.
        location: the location to search for, e.g. New York, NY.
    """

    def __init__(self, keyword, location, uri='https://yellowpages.com'):
        self.uri = uri
        self.keyword = keyword
        self.location = location
        self.session = requests.Session()
        self.session.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:68.0) Gecko/20100101 Firefox/68.0',
            'Accept-Language': 'en-US,en;q=0.5',
            'Connection': 'keep-alive'
        }
        self.logger = logging.getLogger('scrape.webpage')
        self.results = []

    def _get_uri(self, search=None):
        """Creates the full url to fetch results from.

        Includes any keyword, location and page parameters.

        Args:
            search: A dict mapping 
        """
        uri = self.uri
        if search:
            uri += '/search?{}'.format(parse.urlencode(search))
            self.logger.debug(uri)
        return uri        

    def _get_response(self, keyword, location, page=None):
        """Returns a response object.
        Args:
            keyword: Search terms against yellowpages.com.
            location: the location to search for, e.g. New York, NY.
        Returns:
            Response object.
        """

        search_terms = [('search_terms', keyword), ('geo_location_terms', location)]
        if page is not None:
            search_terms.append(('page', page))
        uri = self._get_uri(search_terms)
        try:
            #time.sleep(3)
            response = self.session.get(uri, timeout=10)
            response.raise_for_status()
        except:
            response = None
        return response

    def _get_num_pages(self, parser):
        try:
            pagination = parser.find(class_='pagination')
            regex = re.search(r'(\d+)', pagination.p.text)
            num_results = int(regex.groups()[0])
            return math.ceil(num_results / 30)
        except:
            return 1

    def _match_email(self, content):
        email_list = re.findall(
                r'mailto:([a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+)', content)
        if not email_list:
            email_list = re.findall(
                r'([a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+)', content)
        if email_list:
            return email_list
        else:
            return []
    
    def _get_email_address(self, uri):
        """Scrapes the target URI for one or more email addresses

        Args:
            uri: The uri to scrape for.

        Returns:
            One or more email address, comma in separated format.
        """
        
        with requests.Session() as session:
            try:
                self.logger.debug(f'Uri: {uri}')
                try:
                    response = session.get(uri, timeout=10)
                    response.raise_for_status()
                except:
                    response = None
                if response is not None:
                    email_list = self._match_email(response.text)
                    parser = BeautifulSoup(response.text, 'html5lib')
                    for link in parser.find_all('a'):
                        try:
                            if re.search(r'contact', link['href']):
                                if re.match(r'^/', link['href']):
                                    link['href'] = uri + link['href']
                                elif re.match(r'^c', link['href']):
                                    link['href'] = uri + '/' + link['href']
                                logging.debug('Contact page uri: {}'.format(link['href']))
                                contact_page = session.get(link['href'], timeout=10)
                                email_list += self._match_email(contact_page.text)
                        except:
                            logging.debug('Link has no \'href\' attribute')
                    if email_list:
                        return ', '.join(set(email_list))
            except requests.exceptions.ConnectTimeout:
                self.logger.debug(f'Session timeout: {uri}')
                return ''
            except requests.exceptions.HTTPError:
                self.logger.debug(f'HTTP Error occured - Response status: {response.status_code}')
                return ''
            except:
                self.logger.debug('An unknown error occured')
                return ''

    def _get_results(self, response):
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
            if website:
                email = self._get_email_address(website)
            else: 
                email = ''
            self.logger.info(f'Local: {locale} || Email: {email}')
            self.logger.debug(f'Name: {name}; Category: {category}; Email: {email}; Phone: {phone}; ' + 
                f'Street: {street}; Locality: {locale}; Website: {website}; Link: {link}')
            self.results.append({'BusinessName': name, 'Category': category, 
                            'Email': email, 'Phone': phone,'Street': street, 
                            'Locale': locale, 'Website': website, 'Link': link})
                
    def _get_lead_list(self):
        threads = []
        response = self._get_response(self.keyword, self.location)
        if response is not None:
            parser = BeautifulSoup(response.text, 'html5lib')
            num_pages = self._get_num_pages(parser)
            self.logger.info(f'{num_pages} total pages of results')
            for num in range(1, num_pages):
                self.logger.info(f'Scraping page {num}...')
                response = self._get_response(self.keyword, self.location, num)
                if response is not None:
                    thread = threading.Thread(target=self._get_results, args=(response,))
                    threads.append(thread)
                    thread.start()
                    time.sleep(1)
            for thread in threads:
                thread.join()

    def get_leads(self):
        self._get_lead_list()
        return self.results

def main():
    parser = argparse.ArgumentParser(description='Sales lead scraper')
    parser.add_argument('-k', '--keyword', required=True, nargs='+')
    parser.add_argument('-l', '--location', required=True, nargs='+')
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
    
    results = []
    for location in args.location:
        for keyword in args.keyword:
            logger.info(f'Location: {location}')
            logger.info(f'Keyword: {keyword}')
            web_page = WebPage(keyword=keyword, location=location)
            results += web_page.get_leads()
    with open(args.output_file, 'a', newline='') as csvfile:
        fieldnames = ['BusinessName', 'Category', 'Email', 'Phone', 'Street', 
                    'City', 'State', 'Zip', 'Website', 'Link']
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