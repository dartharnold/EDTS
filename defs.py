import os

name = "EDTS"

version_major = 1
version_minor = 0
version_patch = 0
version_pre   = ''

version = '{}.{}.{}{}'.format(version_major, version_minor, version_patch, version_pre)

default_db_file = os.path.normpath('data/edts.db')
