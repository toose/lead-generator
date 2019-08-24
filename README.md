# Lead Generator

A python module for scraping business information from yellowpages.com.

Based upon a keyword and a location, this module will scrape:
* Business names
* Business categories
* Phone numbers
* Address information
* Email addresses
* Website links
* Yellowpage website link (relative)

## Getting Started
Clone the repository and then install prerequisites using Pipenv:

    pipenv install

Alternatively, you can install the prerequisite modules manually:

    pip install requests bs4 html5lib

## Running the code
Run the script by specifying a keyword, location, output filename and verbosity level (optional):
    
    python3 leadgen.py -k 'Electrical Supply Store' -l 'New York, NY' -o output.csv -vv

## License
This project is license under the MIT license - see the [LICENSE.md](https://github.com/toose/lead-generator/blob/master/LICENSE.md).
