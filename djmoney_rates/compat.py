try:
    from urllib2 import urlopen
except ImportError:
    from urllib.request import urlopen

try:
    from urllib2 import URLError
except ImportError:
    from urllib.error import URLError

try:
    from urllib import urlencode
except ImportError:
    from urllib.parse import urlencode
