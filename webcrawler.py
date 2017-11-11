import json
import socket
from html.parser import HTMLParser
import sys
import queue
import gzip


BASE_URL = "fring.ccs.neu.edu" # base url; only crawl sites with this as base
secret_flag_attrs = [('class', 'secret_flag'), ('style', 'color:red')]

# username = sys.argv[1]
# password = sys.argv[2]
# cookie = None               # set cookie after login

queued = queue.Queue()      # list of urls to crawl
visited = []                # list of urls already crawled

flags = []                  # secret flags

username = '1962838'
password = '9VGKTMDC'

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



# helper method to separate response headers and convert to json,
# and decompress the response body
def parse_response(data):
    start_idx = data.find('\r\n\r\n'.encode('utf-8'))

    # headers include everything up to CRLF
    resp_header = json.loads(data[:start_idx].decode('utf-8'))

    # response body begins after CRLF
    resp_body = data[start_idx+4:]
    resp_body = gzip.decompress(resp_body).decode('utf-8')

    return resp_header, resp_body



parser = CustomHTMLParser()

# setup socket
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.settimeout(10.30)
try:
    sock.connect(('fring.ccs.neu.edu', 80))
except Exception as e: 
    print("Socket connection error: %s" % e)


print("Requesting login page")
get_login = ('GET /accounts/login/?next=/fakebook/ HTTP/1.1\n' +
            'Host: fring.ccs.neu.edu\nAccept-Encoding: gzip, deflate\n' +
            'Connection: keep-alive\n\n')
print(get_login)
sock.send(get_login.encode('utf-8'))

data = (sock.recv(10000))
resp_header, resp_body = parse_response(data)
print("GET LOGIN PAGE HEADERS: ", str(resp_header))
print("GET LOGIN PAGE BODY: ", resp_body)
parser.feed(resp_body)
# print("waiting for response")
# data = (sock.recv(200000000))
# data +=(sock.recv(200000000))
# data = data.decode('utf-8')
# # print(data)
# parser.feed(data)

#
#

# print("waiting for response")
# data = (sock.recv(1500000))
# end = '\r\n\r\n'.encode('utf-8')
# response_idx = data.find(end)+4
# response = data[response_idx:]
# response = gzip.decompress(response)
# print("LOGIN PAGE DATA", response)
# parser.feed(response.decode('utf-8'))
# print("send login")
body = 'id_username=' + username + '&id_password=' + password

# extract csrf token from cookie header
cookie = resp_header['Cookie']
csrf_token = cookie[cookie.find('csrftoken=')+10:]
csrf_token = csrf_token[:csrf_token.find(';')]

post_login = '''POST /accounts/login/ HTTP/1.1
Host: fring.ccs.neu.edu
Content-Type: application/x-www-form-urlencoded
Cookie: csrftoken={0}
Cache-Control: no-cache
Connection: keep-alive
Accept-Encoding: gzip, deflate

password=E0N5X388&username=1946011&csrfmiddlewaretoken={1}\n\n'''.format(csrf_token, csrf_token)
print("Posting login request: ", post_login)
sock.send(post_login.encode('utf-8'))


data2 = (sock.recv(10000))
resp_header, resp_body = parse_response(data2)
print("POST LOGIN RESPONSE HEADER: ", str(resp_header))
print("POST LOGIN RESPONSE BODY: ", resp_body)
sock.shutdown(1)
sock.close()
parser.feed(resp_body)
