import json
import socket
from html.parser import HTMLParser
import sys
import queue


BASE_URL = "fring.ccs.neu.edu" # base url; only crawl sites with this as base
secret_flag_attrs = [('class', 'secret_flag'), ('style', 'color:red')]

username = sys.argv[1]
password = sys.argv[2]
cookie = None               # set cookie after login

queued = queue.Queue()      # list of urls to crawl
visited = []                # list of urls already crawled

flags = []                  # secret flags


class CustomHTMLParser(HTMLParser):
    def __init__(self):
        HTMLParser.__init__(self)
        # if last handled start tag was <h2 class="secret_flag" style="color:red">
        self.flag = False


    def handle_starttag(self, tag, attrs):
        if tag == "a":
            link = [ii[1] for ii in enumerate(attrs) if ii[0] == "href"][0]
            # if begins with base url (either with or without "http://") and not in visited
            if ((link[0,17] == BASE_URL or link[7,24] == BASE_URL) and
                        visited.index(link) == -1):
                queued.put(link)

        # if secret flag tag, set flag to true to handle data correctly
        if tag == "h2" and attrs == secret_flag_attrs:
            self.flag = True


    # def handle_endtag(self, tag):
    #     print("Encountered an end tag:", tag)


    def handle_data(self, data):
        # if the start tag for a secret flag was just handled, record secret flag
        if self.flag:
            flags.append(data)
            self.flag = False


parser = CustomHTMLParser()
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.settimeout(10.30)
print("connecting")
try:
    sock.connect(('google.com',80))
except Exception as e: 
    print("something's wrong %s" % e)
print("sending")
sendthis = 'GET / HTTP/1.0\r\n\r\n'
sock.sendall(sendthis.encode('utf-8'))
print("sent")
print("waiting for response")
data = (sock.recv(1000000))
data = data.decode('utf-8')
print(data)
sock.shutdown(1)
sock.close()
parser.feed(data)
