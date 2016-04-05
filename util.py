import sys

if sys.version_info >= (3, 0):
  import urllib.request
else:
  import urllib2


def read_from_url(url):
  if sys.version_info >= (3, 0):
    return urllib.request.urlopen(url).read().decode("utf-8")
  else:
    return urllib2.urlopen(url).read()


def download_file(url, file):
  if sys.version_info >= (3, 0):
    urllib.request.urlretrieve(url, file)
  else:
    urllib2.urlretrieve(url, file)


def string_bool(s):
  return s.lower() in ("yes", "true", "1")
