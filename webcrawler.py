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

csrf_token = None

class CustomHTMLParser(HTMLParser):
    def __init__(self):
        HTMLParser.__init__(self)
        # if last handled start tag was <h2 class="secret_flag" style="color:red">
        self.flag = False

    def handle_starttag(self, tag, attrs):
        global csrf_token
        if tag == "a":
            link = [ii[1] for ii in attrs if ii[0] == "href"][0]
            print("link ", link)
            # if begins with base url (either with or without "http://") and not in visited
            if link[0] == '/' and link not in visited:
                queued.put(link)

        # if secret flag tag, set flag to true to handle data correctly
        elif tag == "h2" and attrs == secret_flag_attrs:
            self.flag = True

        elif tag == "input" and not csrf_token and ('name', 'csrfmiddlewaretoken') in attrs:
            csrf_token = [ii[1] for ii in attrs if ii[0] == "value"][0]
            #csrf = False
            #for ii in attrs:
        #	if csrf and ii[0] == 'value':
        #	    csrf_token = ii[1]
        #	    break
        #	if ii == ('name', 'csrfmiddlewaretoken'):
        #	    csrf = True

        #  print("csrf token tag: ", csrf_token)

        else:
            return

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
    header_str = data[:start_idx].decode('utf-8').rsplit('\n')

    # first element will be HTTP response code
    resp_code = header_str[0]
    del header_str[0]

    resp_header = {}
    for header in header_str:
        key, sep, value = header.partition(': ')
        resp_header[key] = value


    # response body begins after CRLF
    resp_body = data[start_idx+4:]
    if resp_header.get('Content-Encoding', None):

        resp_body = gzip.decompress(resp_body).decode('utf-8')

    return resp_code, resp_header, resp_body



# get specific value within a header value
# ex: to get csrftoken within cookie header, do get_header_secondary_value(resp_header['Cookie'],'csrftoken')
def get_header_secondary_value(header_val, secondary_key):
    secondary_headers = header_val.rsplit('; ')
    print(secondary_headers)

    for header in secondary_headers:
        key, sep, value = header.partition('=')
        print("header key: ", key, "header value: ", value)
        if key == secondary_key:
            return value



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
resp_code, resp_header, resp_body = parse_response(data)
print("GET LOGIN PAGE RESPONSE CODE: ", resp_code)
print("GET LOGIN PAGE HEADERS: ", str(resp_header))
print("GET LOGIN PAGE BODY: ", resp_body)
parser.feed(resp_body)


# extract csrf token from cookie header
# cookie = resp_header['Cookie']
# csrf_token = cookie[cookie.find('csrftoken=')+10:]
# csrf_token = csrf_token[:csrf_token.find(';')]
print('Set cookie header: ', resp_header['Set-Cookie'])
session_id = get_header_secondary_value(resp_header['Set-Cookie'], 'sessionid')
post_login = '''POST /accounts/login/ HTTP/1.1
Host: fring.ccs.neu.edu
Content-Type: application/x-www-form-urlencoded
Cookie: csrftoken={0}
Cache-Control: no-cache

password=E0N5X388&username=1946011&csrfmiddlewaretoken={1}\n\n'''.format(csrf_token, csrf_token)
print( post_login)
sock.send(post_login.encode('utf-8'))


data2 = (sock.recv(10000000))
resp_code, resp_header, resp_body = parse_response(data2)
print("POST LOGIN RESPONSE CODE: ", resp_code)
print("POST LOGIN RESPONSE HEADER: ", str(resp_header))
print("POST LOGIN RESPONSE BODY: ", resp_body)
parser.feed(resp_body)

fakebook = ('GET /fakebook/ HTTP/1.1\n' +
             'Host: fring.ccs.neu.edu\nAccept-Encoding: gzip, deflate\n' +
             'Connection: keep-alive\n\n')
sock.send(fakebook.encode('utf-8'))

data3 = (sock.recv(100000))
resp_code, resp_header, resp_body = parse_response(data)
print("GET FAKEBOOK RESPONSE CODE: ", resp_code)
print("GET FAKEBOOK HEADERS: ", str(resp_header))
print("GET FAKEBOOK BODY: ", resp_body)
parser.feed(resp_body)

sock.shutdown(1)
sock.close()
