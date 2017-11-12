import socket
from html.parser import HTMLParser
import sys
import queue
import gzip


BASE_URL = "fring.ccs.neu.edu" # base url; only crawl sites with this as base
LOGIN_URL = "/accounts/login/?next=/fakebook/"
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
        global csrf_token, visited, queued
        if tag == "a":
            link = [ii[1] for ii in attrs if ii[0] == "href"][0]
            url = check_valid_url(link)
            # if begins with base url (either with or without "http://") and not in visited
            if url and url not in visited:
                queued.put(url)

        # if secret flag tag, set flag to true to handle data correctly
        elif tag == "h2" and attrs == secret_flag_attrs:
            self.flag = True
            print("FOUND FLAG # {0} !!!!!!".format(len(flags)))

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




# helper method to separate response headers into dict and decompress response body
# return 3-tuple of int response_code, dict headers, string body
# if some error encountered, return 0, 0, 0 (which will cause to try request again)
def parse_response(data):
    try:
        start_idx = data.find('\r\n\r\n'.encode('utf-8'))

        # headers include everything up to CRLF
        header_str = data[:start_idx].decode('utf-8').rsplit('\n')
        # first element will be HTTP response code
        resp_code = int(header_str[0][9:12])


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

        if resp_code == 200:
            parser.feed(resp_body)

        return resp_code, resp_header, resp_body

    except Exception as e:
        return 0, 0, 0



# simple GET request after logged in
# (multiprocessing: add token and sessionid as params)
# return response code of request
def http_get(socket, url, additional_headers=None):
    global csrf_token, session_id, flags

    # send request
    request = ('GET {0} HTTP/1.1\nHost: fring.ccs.neu.edu\n' +
               'Accept-Encoding: gzip, deflate\nConnection: keep-alive\n' +
               'Cookie: csrftoken={1}; sessionid={2}\r\n\r\n').format(url, csrf_token, session_id)
    socket.send(request.encode('utf-8'))

    # receive response
    resp = (socket.recv(10000))
    before = len(flags)
    resp_code, resp_header, resp_body = parse_response(resp)
    if len(flags) != before:
        print("FOUND FLAG {0} AT {1}".format(flags[before], url))


    return resp_code


# re-request the given url after receiving a 500
def retry_after_500(url):
    global csrf_token, session_id, sock
    newsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock = newsock
    sock.settimeout(140.30)
    try:
        sock.connect(('fring.ccs.neu.edu', 80))
    except Exception as e:
        print("Socket connection error: %s" % e)
    #if not login(newsock):
    #    print("ERRRRR")
    request = ('GET {0} HTTP/1.1\nHost: fring.ccs.neu.edu\n' +
               'Accept-Encoding: gzip, deflate\nConnection: keep-alive\n' +
               'Cookie: csrftoken={1}; sessionid={2}\r\n\r\n').format(url, csrf_token, session_id)
    sock.send(request.encode('utf-8'))
    resp = (sock.recv(10000))
    resp_code, resp_header, resp_body = parse_response(resp)

    return handle_response_code(url, resp_code)




# handle the response code of a request for a url
# return True if known response code; otherwise return False
def handle_response_code(url, resp_code):
    if resp_code == 200 or resp_code == 403 or resp_code == 404:
        return True

    elif resp_code == 500 or resp_code == 0:
        return retry_after_500(url)

    elif resp_code == 301:
        # TODO: handle 301 moved permanently
        print("URL {0} 301 moved permanently".format(url))
        return True

    elif resp_code == 302:
        # TODO: handle 302 redirect
        print("URL {0} 302 redirect".format(url))
        return True

    else:
        print("URL {0}  response code: {1}".format(url, resp_code))
        return False



# crawl the url
# return True on success
# return False if returned an unknown response code
def crawl(socket, url):
    resp_code = http_get(socket, url)
    return handle_response_code(url, resp_code)



# login to fakebook with given socket (for potential multiprocessing)
# return True on success
def login(socket):
    global session_id

    body = 'password=E0N5X388&username=1946011&csrfmiddlewaretoken={0}'.format(csrf_token)
    post_login = ('POST /accounts/login/?next=/fakebook/ HTTP/1.1\r\n'+
                  'Host: fring.ccs.neu.edu\r\n'+
                  'Content-Type: application/x-www-form-urlencoded\r\n'+
                  'Cookie: csrftoken={0}\r\n'+
                  'Cache-Control: no-cache\r\n'+
                  'Connection: keep-alive\r\n'+
                  'Accept-Encoding: gzip, deflate\r\n'+
                  'Content-Length: {1}\r\n\r\n{2}\r\n\r\n').format(csrf_token, len(body), body)

    socket.send(post_login.encode('utf-8'))

    data = (socket.recv(1000))
    resp_code, resp_header, resp_body = parse_response(data)

    # if login successful, should redirect
    if resp_code == 302:
        parser.feed(resp_body)
        # set session_id to use for all requests
        session_id = get_header_secondary_value(resp_header['Set-Cookie'], 'sessionid')

        # navigate to redirect location
        redirect = check_valid_url(resp_header['Location'])
        return crawl(socket, redirect)

    return False





parser = CustomHTMLParser()

# setup socket
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.settimeout(140.30)
try:
    sock.connect(('fring.ccs.neu.edu', 80))
except Exception as e:
    print("Socket connection error: %s" % e)


# crawl login page for csrf token
crawl(sock, LOGIN_URL)

# login
login_response_code = login(sock)
if not login_response_code:
    print("Login error: response code ", login_response_code)

print("begin crawl")
# crawl queued urls until all flags found
while not queued.empty():
    if len(flags) == 5:
        break

    next_url = queued.get()
    if next_url not in visited:
        visited.append(next_url)
        # crawl(sock, next_url)
        if not crawl(sock, next_url):
            print("queued: ", list(queued.queue))
            print("visited: ", visited)
            break


sock.shutdown(1)
sock.close()
print(flags)
