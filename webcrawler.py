import json
import socket
from html.parser import HTMLParser

class CustomHTMLParser(HTMLParser):
    def handle_starttag(self, tag, attrs):
        print("Encountered a start tage:", tag)

    def handle_endtag(self, tag):
        print("Encountered an end tag:", tag)

    def handle_data(self, data):
        print("Encountered some data:", data)
        
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
