import os
import sys

name = "EDTS"

version_major = 1
version_minor = 1
version_patch = 0
version_pre   = ''

version = '{}.{}.{}{}'.format(version_major, version_minor, version_patch, version_pre)

log_dateformat = "%H:%M:%S"

try:
  default_path = os.path.dirname(os.path.abspath(__file__))
except NameError:
  default_path = os.path.abspath(sys.path[0])

default_db_file = os.path.normpath('data/edts.db')
default_db_path = os.path.join(default_path, default_db_file)
use_edsm = 'never'
edsm_sphere_radius = 50
edsm_sphere_inner = 0
