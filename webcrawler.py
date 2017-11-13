import socket
import sys
import gzip
import multiprocessing

import utils
import html_parser

BASE_URL = "fring.ccs.neu.edu" # base url; only crawl sites with this as base
LOGIN_URL = "/accounts/login/?next=/fakebook/"

# username = sys.argv[1]
# password = sys.argv[2]


username = '1962838'
password = '9VGKTMDC'



# helper method to separate response headers into dict and decompress response body
# return 3-tuple of int response_code, dict headers, string body
# if some error encountered, return 0, 0, 0 (which will cause to try request again)
def parse_response(data, parser):
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
def http_get(crawler, url, additional_headers=None):
    # send request
    request = ('GET {0} HTTP/1.1\nHost: fring.ccs.neu.edu\n' +
               'Accept-Encoding: gzip, deflate\nConnection: keep-alive\n' +
               'Cookie: csrftoken={1}; sessionid={2}\r\n\r\n').format(url, crawler.csrf_token, crawler.session_id)
    crawler.sock.send(request.encode('utf-8'))

    # receive response
    resp = (crawler.sock.recv(10000))
    resp_code, resp_header, resp_body = parse_response(resp, crawler.parser)

    return resp_code


# re-request the given url after receiving a 500
def retry_after_500(crawler, url):
    # global csrf_token, session_id, sock

    # close old socket
    crawler.sock.shutdown(1)
    crawler.sock.close()

    # open new socket for crawler
    crawler.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    crawler.sock.settimeout(140.30)
    crawler.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
    try:
        crawler.sock.connect(('fring.ccs.neu.edu', 80))
    except Exception as e:
        print("Socket connection error: %s" % e)

    request = ('GET {0} HTTP/1.1\nHost: fring.ccs.neu.edu\n' +
               'Accept-Encoding: gzip, deflate\nConnection: keep-alive\n' +
               'Cookie: csrftoken={1}; sessionid={2}\r\n\r\n').format(url, crawler.csrf_token, crawler.session_id)
    crawler.sock.send(request.encode('utf-8'))
    resp = (crawler.sock.recv(10000))
    resp_code, resp_header, resp_body = parse_response(resp, crawler.parser)

    return handle_response_code(crawler, url, resp_code)




# handle the response code of a request for a url
# return True if known response code; otherwise return False
def handle_response_code(crawler, url, resp_code):
    if resp_code == 200 or resp_code == 403 or resp_code == 404:
        return True

    elif resp_code == 500 or resp_code == 0:
        return retry_after_500(crawler, url)

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
def crawl(crawler, url):
    resp_code = http_get(crawler, url)
    return handle_response_code(crawler, url, resp_code)



# login to fakebook with given socket (for potential multiprocessing)
# return True on success
def login(socket, parser):
    # get login page to get csrf token		
    get_login = ('GET /accounts/login/?next=/fakebook/ HTTP/1.1\n' +
                 'Host: fring.ccs.neu.edu\nAccept-Encoding: gzip, deflate\n' +
                 'Connection: keep-alive\n\n')
    socket.send(get_login.encode('utf-8'))

    data = (socket.recv(10000))
    resp_code, resp_header, resp_body = parse_response(data, parser)
    
    parser.feed(resp_body)
    visited.append('/accounts/login/?next=/fakebook/')
    
    body = 'password=E0N5X388&username=1946011&csrfmiddlewaretoken={0}'.format(parser.csrf_token)
    post_login = ('POST /accounts/login/?next=/fakebook/ HTTP/1.1\r\n'+
                  'Host: fring.ccs.neu.edu\r\n'+
                  'Content-Type: application/x-www-form-urlencoded\r\n'+
                  'Cookie: csrftoken={0}\r\n'+
                  'Cache-Control: no-cache\r\n'+
                  'Connection: keep-alive\r\n'+
                  'Accept-Encoding: gzip, deflate\r\n'+
                  'Content-Length: {1}\r\n\r\n{2}\r\n\r\n').format(parser.csrf_token, len(body), body)

    socket.send(post_login.encode('utf-8'))

    data = (socket.recv(1000))
    resp_code, resp_header, resp_body = parse_response(data, parser)

    # if login successful, should redirect
    if resp_code == 302:
        parser.feed(resp_body)
        # set session_id to use for all requests
        parser.session_id = utils.get_header_secondary_value(resp_header['Set-Cookie'], 'sessionid')
        redirect = utils.check_valid_url(resp_header['Location'])

        # navigate to redirect location
        def get_login_redirect():
            redirect_get = ('GET {0} HTTP/1.1\n' +
                            'Host: fring.ccs.neu.edu\nAccept-Encoding: gzip, deflate\n' +
                            'Connection: keep-alive\nCookie: csrftoken={1}; sessionid={2}' +
                            '\n\n').format(redirect, parser.csrf_token, parser.session_id)
            socket.send(redirect_get.encode('utf-8'))
            data = (socket.recv(1000))
            resp_code, resp_header, resp_body = parse_response(data, parser)
            return resp_code


        res = get_login_redirect()
        while res != 200:
            res = get_login_redirect()

        return True


    return False



class Crawler(multiprocessing.Process):
    def __init__(self, queued, visited, cookie, flags):
        multiprocessing.Process.__init__(self)
        self.queued = queued
        self.visited = visited
        # import pdb; pdb.set_trace()
        self.csrf_token = cookie['csrf']
        self.session_id = cookie['session_id']
        self.flags = flags
        self.parser = html_parser.CustomHTMLParser(queued, visited, self.csrf_token, flags)

        # setup socket
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.settimeout(140.30)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
        try:
            self.sock.connect(('fring.ccs.neu.edu', 80))
        except Exception as e:
            print("Socket connection error: %s" % e)


    def run(self):
        proc_name = self.name
        # print("Begin process ", proc_name)

        while not self.queued.empty():
            if len(flags) == 5:
                break

            next_url = self.queued.get()
            if next_url not in self.visited:
                # print(next_url, proc_name)
                self.visited.append(next_url)
                crawl(self, next_url)

        self,queued.cancel_join_thread()




# Establish communication queues
queued = multiprocessing.Queue()
visited = multiprocessing.Manager().list()
flags = multiprocessing.Manager().list()
parser = html_parser.CustomHTMLParser(queued, visited, None, flags)

# setup first socket (for login and cookie setup)
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.settimeout(140.30)
sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
try:
    sock.connect(('fring.ccs.neu.edu', 80))
except Exception as e:
    print("Socket connection error: %s" % e)


# login
login_response_code = login(sock, parser)
if not login_response_code:
    print("Login error: response code ", login_response_code)

cookie = {'csrf': parser.csrf_token, 'session_id': parser.session_id}

# Start consumers
num_crawlers = 10#multiprocessing.cpu_count() * 2
crawlers = [Crawler(queued, visited, cookie, flags)
             for i in range(num_crawlers)]

for cc in crawlers:
    cc.start()

# Wait for all crawlers to finish
for cc in crawlers:
    # print("join crawler ", cc.name)
    cc.join()

sock.shutdown(1)
sock.close()
