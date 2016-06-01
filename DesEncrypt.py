# -*- coding: utf-8 -*-
# @Author: edward
# @Date:   2016-05-30 16:09:24
# @Last Modified by:   edward
# @Last Modified time: 2016-06-01 10:47:21
import base64
from Crypto.Cipher import DES
from Crypto.Hash import MD5
from Crypto import Random
# ==========
DES_PUBLIC_ENCRYPT_KEY = "6Ta4OaHZdpA="; #DES加密key; using the first 8 bytes in key
DES_PRIVATE_ENCRYPT_KEY ="o0al4OaEWBzA1";

class DesEncrypt(object):

    replaceStr = [
        ("+", "[j]"), 
        ("/", "[x]"),
        ("=", "[d]"),        
    ]
    def __init__(self, key, *args, **kw):
        super(DesEncrypt, self).__init__(*args, **kw)
        self.set_key(key)

    def set_key(self, key):
        self._key = key[:8]

    @property
    def key(self):
        return self._key

    def _replace_key_by_value(self, input_str):
        output_str = input_str
        for key, value in self.replaceStr:
            output_str = output_str.replace(key, value)
        return output_str

    def _replace_value_by_key(self, input_str):
        output_str = input_str
        for key, value in self.replaceStr:
            output_str = output_str.replace(value, key)
        return output_str

    def decrypt(self, message):
        message = self._replace_value_by_key(message)
        message = base64.b64decode(message)
        message =  self.getDesCode(message)
        return message

    def encrypt(self, plaintext):
        plaintext = self.getEncCode(plaintext)
        plaintext = base64.b64encode(plaintext)
        plaintext = self._replace_key_by_value(plaintext)
        return plaintext


    def getDesCode(self, byteD):
        obj = DES.new(self.key)
        des = obj.decrypt(byteD)
        return des

    def getEncCode(self, byteS):
        obj = DES.new(self.key)
        enc = obj.encrypt(byteS)
        return enc

def md5(text):
    h = MD5.new()
    h.update(text)
    hashed = h.hexdigest()
    return hashed
    # print hashed
    # for i in hashed:
    #     val = int(i, 16) & 0xff
    #     if val < 16:
    #         value.append("0");
    #     value.append(hex(val)[2:])
    # return value

    
if __name__ == '__main__':
    '''
    raw password       frontend-encrypted           final hashed 
                    eX[j]4lwGjrCQ4ZgsTEp1PIg[d][d]
    "xiaoting1" -> "eX[j]4lwGjrCQ4ZgsTEp1PIg==" -> "f482128b3e62c13a743b62ca710c3042"
    '''
    public = DesEncrypt(DES_PUBLIC_ENCRYPT_KEY)
    # public.encrypt('xiaoting1')
    private = DesEncrypt(DES_PRIVATE_ENCRYPT_KEY)
    decrypted = public.decrypt("eX[j]4lwGjrCQ4ZgsTEp1PIg==")
    encrypted = private.encrypt(decrypted)
    print md5(encrypted)

