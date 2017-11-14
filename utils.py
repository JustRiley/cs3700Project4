#!/usr/bin/python3
BASE_URL = "fring.ccs.neu.edu" # base url; only crawl sites with this as base

# helper method to check if the url is valid
# returns url without the base url if valid
# returns None if invalid url
def check_valid_url(url):
    if url[0] == '/':
        return url
    elif url[7:24] == BASE_URL or url[:17] == BASE_URL:
        return url.replace(BASE_URL, '').replace('http://', '')
    else:
        return None


# get specific value within a header value
# ex: to get csrftoken within cookie header, do get_header_secondary_value(resp_header['Cookie'],'csrftoken')
def get_header_secondary_value(header_val, secondary_key):
    secondary_headers = header_val.rsplit('; ')

    for header in secondary_headers:
        key, sep, value = header.partition('=')
        if key == secondary_key:
            return value



