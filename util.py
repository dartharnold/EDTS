import sys

if sys.version_info >= (3, 0):
  import urllib.request
else:
  import urllib2


def open_url(url):
  if sys.version_info >= (3, 0):
    return urllib.request.urlopen(url)
  else:
    return urllib2.urlopen(url)

def read_stream(stream, limit = None):
  if sys.version_info >= (3, 0):
    return stream.read(limit).decode("utf-8")
  else:
    return stream.read(limit)

def read_from_url(url):
  return read_stream(open_url(url))


def is_interactive():
  return hasattr(sys, 'ps1')


def is_str(s):
  if sys.version_info >= (3, 0):
    return isinstance(s, str)
  else:
    return isinstance(s, basestring)


def download_file(url, file):
  if sys.version_info >= (3, 0):
    urllib.request.urlretrieve(url, file)
  else:
    urllib2.urlretrieve(url, file)


def string_bool(s):
  return s.lower() in ("yes", "true", "1")
