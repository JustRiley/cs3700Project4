# cs3700Project4
The goal of this project was to create a webcrawler that would crawl a fake social media site, searching for secret flags.
The first step was to login to the website by issuing an HTTP POST request. In addition to passing username and password.
The request also needs to pass along a 'csrfmiddlewaretoken' that the server uses to do CSRF verification. Then, once logged
in, with the help of an HTML parser gather all of the links. Making sure to only queue links that are in the correct domain,
and have not already been visited. One issue that we had to account for was when the server returns a response code of 500.
When this happens the response header contains a close connection header. So this means that our crawler needs to retry sending
the message again, until it receives a response code of 200. While the parser is looking for links, it is also looking for the
tag that contains the secret flags. Once it finds one it adds it to the list and continues until all 5 flags are found. Once we
were confident in our crawler working on a single thread, we moved to implement multithreading since on a single thread it can 
take quite a while for the crawler to find all of the flags. 
