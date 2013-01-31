from binascii import crc32

from breezeminder.app import app
from breezeminder.util.shorturls import default_base


@app.cache.memoize(timeout=3600)
def shortcode(value):
    value = ''.join([app.config.get('SECRET_KEY', ''), value])
    crc32_val = abs(crc32(value))
    return default_base.from_decimal(int(str(crc32_val), 16)).upper()
