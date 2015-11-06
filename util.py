import sys
import urllib
if sys.version_info >= (3, 0):
  import urllib.request

def download_file(url, file):
  if sys.version_info >= (3, 0):
    urllib.request.urlretrieve(url, file)
  else:
    urllib.urlretrieve(url, file)