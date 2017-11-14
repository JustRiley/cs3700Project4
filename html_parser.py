#!/usr/bin/python3
from html.parser import HTMLParser
import utils

secret_flag_attrs = [('class', 'secret_flag'), ('style', 'color:red')]


class CustomHTMLParser(HTMLParser):
    def __init__(self, queued, visited, csrf_token, flags):
        HTMLParser.__init__(self)
        # if last handled start tag was <h2 class="secret_flag" style="color:red">
        self.flag_found = False

        self.queued = queued
        self.visited = visited
        self.csrf_token = csrf_token
        self.session_id = None
        self.flags = flags

    def handle_starttag(self, tag, attrs):
        if tag == "a":
            link = [ii[1] for ii in attrs if ii[0] == "href"][0]
            url = utils.check_valid_url(link)
            # if begins with base url (either with or without "http://") and not in visited
            if url and url not in self.visited:
                self.queued.put(url)

        # if secret flag tag, set flag to true to handle data correctly
        elif tag == "h2" and attrs == secret_flag_attrs:
            self.flag_found = True

        elif tag == "input" and not self.csrf_token and ('name', 'csrfmiddlewaretoken') in attrs:
            self.csrf_token = [ii[1] for ii in attrs if ii[0] == "value"][0]

        else:
            return

    def handle_data(self, data):
        # if the start tag for a secret flag was just handled, record secret flag
        if self.flag_found:
            self.flags.append(data)
            print(data.split(" ")[1])
            self.flag_found = False
