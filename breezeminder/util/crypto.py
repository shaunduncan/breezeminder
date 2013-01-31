import base64

from hashlib import md5
from Crypto.Cipher import AES

from breezeminder.app import app


BLOCK_SIZE = 32
PAD_STRING = '>'
CIPHER_KEY = md5(app.config['SECRET_KEY']).hexdigest()
AES_CIPHER = AES.new(CIPHER_KEY, AES.MODE_ECB)


def _pad(string):
    pad_string = (BLOCK_SIZE - len(string) % BLOCK_SIZE) * PAD_STRING
    return '%s%s' % (string, pad_string)


@app.cache.memoize(timeout=3600)
def encrypt(string):
    return base64.b64encode(AES_CIPHER.encrypt(_pad(string)))


@app.cache.memoize(timeout=3600)
def decrypt(string):
    return AES_CIPHER.decrypt(base64.b64decode(string)).rstrip(PAD_STRING)
