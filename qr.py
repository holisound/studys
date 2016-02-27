# -*- coding: utf-8 -*-
# @Author: edward
# @Date:   2016-02-27 17:52:05
# @Last Modified by:   edward
# @Last Modified time: 2016-02-27 20:21:45
from hashlib import md5
import base64
import random
import qrcode
import io

def md5_hash(raw):
    hashed = md5(raw).hexdigest()
    return hashed
    
def encrypt(raw):
    hashed = md5_hash(raw)  
    start = random.randint(0, 16)
    stop = start + random.randint(0, 16)
    x = stop - start
    while (x < 8) or (x > 12) :
      start = random.randint(0, 16)
      stop = start + random.randint(0, 16)
      x = stop - start
    index = slice(start, stop)
    return base64.b64encode(hashed[index])

def decrypt(secret):
  return base64.b64decode(secret)



def save_bytes(raw):
  qr = qrcode.QRCode(
      version=1,
      error_correction=qrcode.constants.ERROR_CORRECT_L,
      box_size=10,
      border=0,
  )
  qr.add_data(raw)
  qr.make(fit=True)
  img = qr.make_image()
  bio = io.BytesIO()
  img.save(bio)
  return bio
