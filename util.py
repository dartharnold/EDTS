import sys
import urllib

if sys.version_info >= (3, 0):
  import urllib.request


def is_str(s):
  if sys.version_info >= (3, 0):
    return isinstance(s, str)
  else:
    return isinstance(s, basestring)

def download_file(url, file):
  if sys.version_info >= (3, 0):
    urllib.request.urlretrieve(url, file)
  else:
    urllib.urlretrieve(url, file)


def string_bool(s):
  return s.lower() in ("yes", "true", "1")
