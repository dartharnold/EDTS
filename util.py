import defs
import logging
import os
import platform
import re
import ssl
import sys

if sys.version_info >= (3, 0):
  import urllib.parse
  import urllib.request
  import urllib.error
else:
  import urllib2
  import urllib
  import urlparse

log = logging.getLogger("util")

USER_AGENT = '{}/{}'.format(defs.name, defs.version)

# Match a float such as "33", "-33", "-33.1"
_rgxstr_float = r'[-+]?\d+(?:\.\d+)?'
# Match a set of coords such as "[33, -45.6, 78.910]"
_rgxstr_coords = r'^\[\s*(?P<x>{0})\s*[,/]\s*(?P<y>{0})\s*[,/]\s*(?P<z>{0})\s*\](?:=(?P<name>.+))?$'.format(_rgxstr_float)
# Compile the regex for faster execution later
_regex_coords = re.compile(_rgxstr_coords)

def parse_coords(sysname):
  rx_match = _regex_coords.match(sysname)
  if rx_match is not None:
    # If it matches, make a fake system and station at those coordinates
    try:
      cx = float(rx_match.group('x'))
      cy = float(rx_match.group('y'))
      cz = float(rx_match.group('z'))
      name = rx_match.group('name') if rx_match.group('name') is not None else sysname
      return (cx, cy, cz, name)
    except Exception as ex:
      log.debug("Failed to parse manual system: {}".format(ex))
  return None


def open_url(url):
  if sys.version_info >= (3, 0):
    # Specify our own user agent as Cloudflare doesn't seem to like the urllib one
    request = urllib.request.Request(url, headers={'User-Agent': USER_AGENT})
    try:
      return urllib.request.urlopen(request)
    except urllib.error.HTTPError as err:
      log.error("Error {0} opening {1}: {2}".format(err.code, url, err.reason))
      return None
  else:
    sslctx = ssl.SSLContext(ssl.PROTOCOL_TLSv1)
    # If we're on OSX with OpenSSL 0.9.x, manually specify preferred ciphers so CloudFlare can negotiate successfully
    if platform.system() == 'Darwin' and ssl.OPENSSL_VERSION_INFO[0] < 1:
      sslctx.set_ciphers("ECCdraft:HIGH:!aNULL")
    # Specify our own user agent as Cloudflare doesn't seem to like the urllib one
    request = urllib2.Request(url, headers={'User-Agent': USER_AGENT})
    try:
      return urllib2.urlopen(request, context=sslctx)
    except urllib2.HTTPError as err:
      log.error("Error {0} opening {1}: {2}".format(err.code, url, err.reason))
      return None

def read_stream_line(stream):
  if sys.version_info >= (3, 0):
    return stream.readline().decode("utf-8")
  else:
    return stream.readline()

def read_stream(stream, limit = None):
  if sys.version_info >= (3, 0):
    return stream.read(limit).decode("utf-8")
  else:
    return stream.read(-1 if limit is None else limit)

def read_from_url(url):
  return read_stream(open_url(url))

def path_to_url(path):
  if sys.version_info >= (3, 0):
    return urllib.parse.urljoin('file:', urllib.request.pathname2url(os.path.abspath(path)))
  else:
    return urlparse.urljoin('file:', urllib.pathname2url(os.path.abspath(path)))


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


# 32-bit hashing algorithm found at http://papa.bretmulvey.com/post/124027987928/hash-functions
# Seemingly originally by Bob Jenkins <bob_jenkins-at-burtleburtle.net> in the 1990s
def jenkins32(key):
  key += (key << 12)
  key &= 0xFFFFFFFF
  key ^= (key >> 22)
  key += (key << 4)
  key &= 0xFFFFFFFF
  key ^= (key >> 9)
  key += (key << 10)
  key &= 0xFFFFFFFF
  key ^= (key >> 2)
  key += (key << 7)
  key &= 0xFFFFFFFF
  key ^= (key >> 12)
  return key


# Grabs the value from the first N bits, then return a right-shifted remainder
def unpack_and_shift(value, bits):
  return (value >> bits, value & (2**bits-1))

# Shifts existing data left by N bits and adds a new value into the "empty" space
def pack_and_shift(value, new_data, bits):
  return (value << bits) + (new_data & (2**bits-1))

# Interleaves two values, starting at least significant bit
# e.g. (0b1111, 0b0000) --> (0b01010101)
def interleave(val1, val2, maxbits):
  output = 0
  for i in range(0, maxbits//2 + 1):
    output |= ((val1 >> i) & 1) << (i*2)
  for i in range(0, maxbits//2 + 1):
    output |= ((val2 >> i) & 1) << (i*2 + 1)
  return output & (2**maxbits - 1)

# Deinterleaves two values, starting at least significant bit
# e.g. (0b00110010) --> (0b0100, 0b0101)
def deinterleave(val, maxbits):
  out1 = 0
  out2 = 0
  for i in range(0, maxbits, 2):
    out1 |= ((val >> i) & 1) << (i//2)
  for i in range(1, maxbits, 2):
    out2 |= ((val >> i) & 1) << (i//2)
  return (out1, out2)
