import json
import socket
import select
from html.parser import HTMLParser
token = 'no token?'
responseHeader = 'no response'
username = '1962838'
password = '9VGKTMDC'

class CustomHTMLParser(HTMLParser):
    def handle_starttag(self, tag, attrs):
        print("")

    def handle_endtag(self, tag):
        print("")

    def handle_data(self, data):
        if("HTTP" in data):
            global responseHeader
            responseHeader = data
    def unknown_decl(self, data):
        print("data ?", data)
        
parser = CustomHTMLParser()
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.settimeout(10.30)
print("connecting")
try:
    sock.connect(('fring.ccs.neu.edu',80))
except Exception as e: 
    print("something's wrong %s" % e)
print("sending")
sendthis = 'GET /accounts/login/?next=/fakebook/ HTTP/1.1\nHost: fring.ccs.neu.edu\n\n'
sock.send(sendthis.encode('utf-8'))
print("sent")
print("waiting for response")
data = (sock.recv(200000000))
data +=(sock.recv(200000000))
data = data.decode('utf-8')
print(data)
parser.feed(data)
headerWords = responseHeader.split("\n")
responseCode = headerWords[0].split(" ")
csrfTokenArray = headerWords[7].split("=")
sessionIdArray = headerWords[8].split("=")
csrfToken = csrfTokenArray[1].split(";")[0]
sessionId = sessionIdArray[1].split(";")[0]
print("response Code",responseCode[1])

print("send login")
body = 'username=' + username + '&password=' + password
sendlogin = ('POST /accounts/login/ HTTP/1.1\n' +'Host: www.fring.ccs.neu.edu:80\nAccept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8\nCookie: csrftoken=' + csrfToken + '; sessionid='+ sessionId +'\nReferer: http://fring.ccs.neu.edu/accounts/login/\nContent-Type: application/x-www-form-urlencoded\nContent-Length: '+ str(len(body)) + '\n\n'+ body +'\n\n')
print(sendlogin)
sock.sendall(sendlogin.encode('utf-8'))
print("sent")
data2 = (sock.recv(1700000))
print("data2", data2.decode('utf-8'))
sock.shutdown(1)
sock.close()

print("CSRFToken", csrfToken)
print("sessionId", sessionId)
#129.10.113.143
