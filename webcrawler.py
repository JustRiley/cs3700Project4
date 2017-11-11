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

queued = queue.Queue()      # list of urls to crawl
visited = []                # list of urls already crawled

flags = []                  # secret flags

username = '1962838'
password = '9VGKTMDC'

csrf_token = None
session_id = None

class CustomHTMLParser(HTMLParser):
    def __init__(self):
        HTMLParser.__init__(self)
        # if last handled start tag was <h2 class="secret_flag" style="color:red">
        self.flag = False

    def handle_starttag(self, tag, attrs):
        global csrf_token
        if tag == "a":
            link = [ii[1] for ii in attrs if ii[0] == "href"][0]
            # if begins with base url (either with or without "http://") and not in visited
            if link[0] == '/' and link not in visited:
                queued.put(link)

        # if secret flag tag, set flag to true to handle data correctly
        elif tag == "h2" and attrs == secret_flag_attrs:
            self.flag = True

        elif tag == "input" and not csrf_token and ('name', 'csrfmiddlewaretoken') in attrs:
            csrf_token = [ii[1] for ii in attrs if ii[0] == "value"][0]

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
    # print("RAW DATA:\n", data)
    start_idx = data.find('\r\n\r\n'.encode('utf-8'))

    # headers include everything up to CRLF
    header_str = data[:start_idx].decode('utf-8').rsplit('\n')

    # first element will be HTTP response code
    resp_code = header_str[0]
    del header_str[0]

    resp_header = {}
    for header in header_str:
        key, sep, value = header.partition(': ')
        resp_header[key] = value.replace('\r', '')

    # TODO: special handling for chunks
    if resp_header.get('Transfer-Encoding', None):
        print('TRANSFER-ENCODING: CHUNKED')

    # response body begins after CRLF
    resp_body = data[start_idx+4:]
    if resp_header.get('Content-Encoding', None):
        resp_body = gzip.decompress(resp_body).decode('utf-8')
    else:
        resp_body = resp_body.decode('utf-8')

    # print('RESPONSE: ')
    # print(resp_code)
    # print(resp_header)
    # print(resp_body)
    return resp_code, resp_header, resp_body



# get specific value within a header value
# ex: to get csrftoken within cookie header, do get_header_secondary_value(resp_header['Cookie'],'csrftoken')
def get_header_secondary_value(header_val, secondary_key):
    secondary_headers = header_val.rsplit('; ')

    for header in secondary_headers:
        key, sep, value = header.partition('=')
        if key == secondary_key:
            return value


# simple GET request after logged in
# (multiprocessing: add token and sessionid as params)
# return resp_code, resp_header, resp_body
def http_get(socket, url, additional_headers=None):
    global csrf_token, session_id
    request = ('GET {0} HTTP/1.1\nHost: fring.ccs.neu.edu\n' +
               'Accept-Encoding: gzip, deflate\nConnection: keep-alive\n' +
               'Cookie: csrftoken={1}; sessionid={2}\r\n\r\n').format(url, csrf_token, session_id)
    socket.send(request.encode('utf-8'))

    resp = (socket.recv(10000))
    return parse_response(resp)


# login to fakebook with given socket (for potential multiprocessing)
# return response code of post request
# after logging in, links have been added to queue, so just begin iterating through those
def login(socket):
    global session_id

    # get login page to get csrf token
    print("Requesting login page")
    get_login = ('GET /accounts/login/?next=/fakebook/ HTTP/1.1\n' +
                 'Host: fring.ccs.neu.edu\nAccept-Encoding: gzip, deflate\n' +
                 'Connection: keep-alive\n\n')
    print(get_login)
    socket.send(get_login.encode('utf-8'))

    data = (socket.recv(10000))
    resp_code, resp_header, resp_body = parse_response(data)
    # print("GET LOGIN PAGE RESPONSE CODE: ", resp_code)
    # print("GET LOGIN PAGE HEADERS: ", str(resp_header))
    # print("GET LOGIN PAGE BODY: ", resp_body)
    parser.feed(resp_body)
    visited.append('/accounts/login/?next=/fakebook/')

    body = 'password=E0N5X388&username=1946011&csrfmiddlewaretoken={0}'.format(csrf_token)
    post_login = ('POST /accounts/login/ HTTP/1.1\r\n'+
                  'Host: fring.ccs.neu.edu\r\n'+
                  'Content-Type: application/x-www-form-urlencoded\r\n'+
                  'Cookie: csrftoken={0}\r\n'+
                  'Cache-Control: no-cache\r\n'+
                  'Connection: keep-alive\r\n'+
                  'Accept-Encoding: gzip, deflate\r\n'+
                  'Content-Length: {1}\r\n\r\n{2}\r\n\r\n').format(csrf_token, len(body), body)

    print(post_login)
    socket.send(post_login.encode('utf-8'))

    data2 = (socket.recv(1000))
    resp_code, resp_header, resp_body = parse_response(data2)
    # print("POST LOGIN RESPONSE CODE: ", resp_code)
    # print("POST LOGIN RESPONSE HEADER: ", str(resp_header))
    # print("POST LOGIN RESPONSE BODY: ", resp_body)

    code = resp_code[9:12]
    # if login successful, should redirect
    if code == '302':
        visited.append('/accounts/login/')
        parser.feed(resp_body)

        # set session_id to use for all requests
        session_id = get_header_secondary_value(resp_header['Set-Cookie'], 'sessionid')

        # navigate to redirect location
        redirect = resp_header['Location']
        resp_code, resp_header, resp_body = http_get(socket, redirect)
        if '200' in resp_code:
            visited.append(redirect)


    return code



parser = CustomHTMLParser()

# setup socket
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.settimeout(10.30)
try:
    sock.connect(('fring.ccs.neu.edu', 80))
except Exception as e:
    print("Socket connection error: %s" % e)

# TODO: crawl links on login page first or last so as not to logout

login_response_code = login(sock)
if login_response_code != '302':
    print("Login error: response code ", login_response_code)

while not queued.empty():
    next_url = queued.get()
    visited.append(next_url)

    # http_get returns 3-tuple
    response = http_get(sock, next_url)
    code = response[0][9:12]
    # TODO: Handle 301, 403, 404, 500
    # if code not in ['200', '302']:
    #
    print("queued: ", list(queued.queue))
    # for q in queued.:

    print("visited: ", visited)


sock.shutdown(1)
sock.close()
