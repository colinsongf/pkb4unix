import rdflib
import os
import urllib
import sys

ENDPOINT_QUERY = os.environ["KNOW_ENDPOINT_QUERY"]
ENDPOINT_UPDATE = os.environ["KNOW_ENDPOINT_UPDATE"]
ENDPOINT_INDIRECT = os.environ["KNOW_ENDPOINT_INDIRECT"]
PROVENANCE_GRAPH = os.environ["KNOW_PROVENANCE_GRAPH"]
NS_GRAPH = os.environ["KNOW_NS_GRAPH"]

NS_KB = rdflib.Namespace("http://www.andonyar.com/rec/2012/pkb/conf#")

contentTypes = {
    "rdf": "application/rdf+xml",
    "ttl": "text/turtle; charset=utf-8",
}

def fileurl2path(url):
    url = urllib.parse.urlparse(url)
    if not url.scheme == "file":
        raise SemPipeException("source must be a file")
    return urllib.request.url2pathname(url.path)

def absurl(url, base=None):
    """Makes an absolute URL from a relative

    In order to make it possible to also use filenames as url, it gets
    quoted first. Only characters not allowed in URLs are quoted. This
    means that certain filenames (those with : or % in their name)
    will not be treated the right way. The reason for this behaviour
    is that an URI like urn:uuid:something could really be a filename
    but is also an absolute URI and has to be interpreted as such."""
    base = base if base else os.path.abspath(".")
    base = "file://" + urllib.request.pathname2url(base)
    url = urllib.parse.quote_plus(url, safe='/:%')
    if base[-1] != "/": base += "/"
    return urllib.parse.urljoin(base, url)

def guessContentType(url):
    return contentTypes[url.rsplit(".", 1)[-1]]

def put_data(data, identifier, contentType, keep_existing=False):
    """data can be an open file, an iterable (since Python 3.2), a bytes or a string object"""
    import http.client
    parsedURL = urllib.parse.urlparse(ENDPOINT_UPDATE)
    connType = { "http": http.client.HTTPConnection, "https": http.client.HTTPSConnection }[parsedURL.scheme]
    connection = connType(parsedURL.hostname, port=parsedURL.port)
    url = "{}?graph={}".format(ENDPOINT_INDIRECT, urllib.parse.quote_plus(identifier))
    connection.request("POST" if keep_existing else "PUT", url, body=data, headers={ 'Content-type': contentType })
    response = connection.getresponse()
    headers = response.getheaders()
    status = response.status
    if not (200 <= status < 300):
        print("{} failed with status {}:".format("POST" if keep_existing else "PUT", status), file=sys.stderr)
        print("\n".join(["{}: {}".format(*h) for h in headers]), file=sys.stderr)
        print("", file=sys.stderr)
        print(response.read().decode("UTF-8"), file=sys.stderr)
    else:
        response.read()
    connection.close()
    return status

def delete_graph(identifier):
    import http.client
    parsedURL = urllib.parse.urlparse(ENDPOINT_UPDATE)
    connType = { "http": http.client.HTTPConnection, "https": http.client.HTTPSConnection }[parsedURL.scheme]
    connection = connType(parsedURL.hostname, port=parsedURL.port)
    url = "{}?graph={}".format(ENDPOINT_INDIRECT, urllib.parse.quote_plus(identifier))
    connection.request("DELETE", url)
    response = connection.getresponse()
    headers = response.getheaders()
    status = response.status
    if not (200 <= status < 300):
        print("DELETE failed with status {}:".format(status), file=sys.stderr)
        print("\n".join(["{}: {}".format(*h) for h in headers]), file=sys.stderr)
        print("", file=sys.stderr)
        print(response.read().decode("UTF-8"), file=sys.stderr)
    else:
        response.read()
    connection.close()
    return status

def get_data(identifier, contentType):
    """data can be an open file, an iterable (since Python 3.2), a bytes or a string object"""
    import http.client
    parsedURL = urllib.parse.urlparse(ENDPOINT_UPDATE)
    connType = { "http": http.client.HTTPConnection, "https": http.client.HTTPSConnection }[parsedURL.scheme]
    connection = connType(parsedURL.hostname, port=parsedURL.port)
    url = "{}?graph={}".format(ENDPOINT_INDIRECT, urllib.parse.quote_plus(identifier))
    connection.request("GET", url, headers={ 'Accept': contentType })
    return HTTPSPARQLResponse(connection)

def kbConnect():
    kb = rdflib.ConjunctiveGraph("SPARQLUpdateStore", identifier='__UNION__')
    kb.open(("http://localhost:8080/openrdf-sesame/repositories/pkb", "http://localhost:8080/openrdf-sesame/repositories/pkb/statements"))
    return kb

class HTTPSPARQLResponse:
    def __init__(self, connection):
        """
        connection must be a HTTP connection with which a request
        has already been sent.
        """
        
        self.connection = connection
        self.response = connection.getresponse()

    def __enter__(self):
        return self;

    def __exit__(self, exc_type, exc_value, traceback):
        self.connection.close()

    def close(self):
        self.connection.close()

    @property
    def headers(self):
        return self.response.getheaders()

    @property
    def status(self):
        return self.response.status

    def read(self, n=-1):
        return self.response.read(n)


