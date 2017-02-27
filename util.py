import collections
import defs
import thirdparty.gzipinputstream as gzis
import logging
import numbers
import os
import platform
import re
import socket
import ssl
import sys
import vector3

if sys.version_info >= (3, 0):
  import urllib.parse
  import urllib.request
  import urllib.error
else:
  import urllib2
  import urllib
  import urlparse

# Slightly ugly classes to allow new-style {} formatting in log messages without always executing them
class _BraceString(str):
  def __mod__(self, other): return self.format(*other)
  def __str__(self): return self
class _StyleAdapter(logging.LoggerAdapter):
  def __init__(self, logger, extra=None): super(_StyleAdapter, self).__init__(logger, extra)
  def process(self, msg, kwargs): return _BraceString(msg), kwargs

def get_logger(name):
  return _StyleAdapter(logging.getLogger(name))

log = get_logger("util")

USER_AGENT = '{}/{}'.format(defs.name, defs.version)

# Match a float such as "33", "-33", "-33.1"
_rgxstr_float = r'[-+]?\d+(?:\.\d+)?'
# Match a set of coords such as "[33, -45.6, 78.910]"
_rgxstr_coords = r'^\[\s*(?P<x>{0})\s*[,/]\s*(?P<y>{0})\s*[,/]\s*(?P<z>{0})\s*\](?:=(?P<name>.+))?$'.format(_rgxstr_float)
# Compile the regex for faster execution later
_regex_float = re.compile('^' + _rgxstr_float + '$')
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
      log.debug("Failed to parse manual system: {}", ex)
  return None


def open_url(url, allow_gzip = True, allow_no_ssl = False):
  response = None
  headers = {'User-Agent': USER_AGENT}
  if allow_gzip:
    headers['Accept-Encoding'] = 'gzip'
  if sys.version_info >= (3, 0):
    # Specify our own user agent as Cloudflare doesn't seem to like the urllib one
    request = urllib.request.Request(url, headers=headers)
    try:
      response = urllib.request.urlopen(request)
    except urllib.error.HTTPError as err:
      log.error("Error {0} opening {1}: {2}", err.code, url, err.reason)
      return None
  else:
    sslctx = None
    try:
      sslctx = ssl.SSLContext(ssl.PROTOCOL_TLSv1)
      # If we're on OSX with OpenSSL 0.9.x, manually specify preferred ciphers so CloudFlare can negotiate successfully
      if platform.system() == 'Darwin' and ssl.OPENSSL_VERSION_INFO[0] < 1:
        sslctx.set_ciphers("ECCdraft:HIGH:!aNULL")
    except Exception as ex:
      if allow_no_ssl:
        log.warning("Failed to create SSL context ({0}), attempting to continue", str(ex))
      else:
        log.error("Failed to create SSL context: {0}", str(ex))
        return None
    # Specify our own user agent as Cloudflare doesn't seem to like the urllib one
    request = urllib2.Request(url, headers=headers)
    try:
      response = urllib2.urlopen(request, context=sslctx)
    except urllib2.HTTPError as err:
      log.error("Error {0} opening {1}: {2}", err.code, url, err.reason)
      return None
  if response.info().get('Content-Encoding') == 'gzip':
    try:
      return gzis.GzipInputStream(response)
    except:
      log.error("Error decompressing {0}", url)
      return None
  else:
    return response

def read_stream_line(stream):
  try:
    if sys.version_info >= (3, 0):
      return stream.readline().decode("utf-8")
    else:
      return stream.readline()
  except socket.error as e:
    if e.errno == socket.errno.ECONNRESET:
      log.warning("Received ECONNRESET while reading line from socket-based stream")
      return None
    else:
      raise

def read_stream(stream, limit = None):
  try:
    if sys.version_info >= (3, 0):
      return stream.read(limit).decode("utf-8")
    else:
      if limit is None and not isinstance(stream, gzis.GzipInputStream):
        limit = -1
      return stream.read(limit)
  except socket.error as e:
    if e.errno == socket.errno.ECONNRESET:
      log.warning("Received ECONNRESET while reading from socket-based stream")
      return None
    else:
      raise

def read_from_url(url, allow_gzip = True, allow_no_ssl = False):
  return read_stream(open_url(url, allow_gzip=allow_gzip, allow_no_ssl=allow_no_ssl))

def write_stream(stream, data):
  try:
    if sys.version_info >= (3, 0):
      return stream.write(data.encode("utf-8"))
    else:
      return stream.write(data)
  except:
    raise

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


def hex2str(s):
  return ''.join(chr(int(s[i:i+2], 16)) for i in range(0, len(s), 2))


def parse_number_or_add_percentage(value, basevalue):
  if value is None or not _regex_float.match(value.strip('%')):
    return None
  if value.endswith('%'):
    return float(basevalue) * (1.0 + (float(value.strip('%')) / 100.0))
  else:
    return float(value)


def int2hex(i, len=64):
  fmtlen = str(int(int(len)/4))
  return ('{0:0'+fmtlen+'X}').format(i)


def get_bytes(s, enc = 'utf-8'):
  if sys.version_info >= (3, 0):
    return bytes(s, enc)
  else:
    return bytes(s)


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


def get_as_position(v):
  if v is None:
    return None
  # If it's already a vector, all is OK
  if isinstance(v, vector3.Vector3):
    return v
  if hasattr(v, "position"):
    return v.position
  if hasattr(v, "centre"):
    return v.centre
  if hasattr(v, "system"):
    return get_as_position(v.system)
  try:
    if len(v) == 3 and all([isinstance(i, numbers.Number) for i in v]):
      return vector3.Vector3(v[0], v[1], v[2])
  except:
    pass
  return None

def flatten(listish):
  return [i for sublist in [listish] for i in sublist] if (isinstance(listish, collections.Iterable) and not is_str(listish)) else [listish]
