import json
import socket
from html.parser import HTMLParser
token = 'no token?'
username = '1962838'
password = '9VGKTMDC'

class CustomHTMLParser(HTMLParser):
    def handle_starttag(self, tag, attrs):
        if(tag == "input"):
            #print("0", attrs)
            if(attrs[1][1] == 'csrfmiddlewaretoken'):
                global token
                token = attrs[2][1]
                print("token: ", token)
        #print("Encountered a start tag:", tag)

    def handle_endtag(self, tag):
        print("")

    def handle_data(self, data):
        print("")
        
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
sock.sendall(sendthis.encode('utf-8'))
print("sent")
print("waiting for response")
data = (sock.recv(1500000))
data = data.decode('utf-8')
#print(data)
parser.feed(data)
print("send login")
body = 'id_username=' + username + '&id_password=' + password
sendlogin = ('POST /accounts/login/ HTTP/1.1\nHost: fring.ccs.neu.edu\nConnection: keep-alive\n' +
             'Cookie: csrftoken=' + token + '\nAccept:text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8'+
             '\nAccept-Encoding:gzip, deflate' +'\nOrigin: http://fring.ccs.neu.edu\nReferer:http://fring.ccs.neu.edu/accounts/login/?next=/fakebook/'+
             '\nContent-Type: application/x-www-form-urlencoded\nContent-Length:'+ str(len(body)) + '\n\n'+ body +'\n\n')
print(sendlogin)
sock.sendall(sendlogin.encode('utf-8'))
print("sent")
data2 = (sock.recv(1700000))
print("data2", data2)
sock.shutdown(1)
sock.close()
print("token",token)

#129.10.113.143
