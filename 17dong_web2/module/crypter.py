#!/usr/bin/env python
#-*-coding:utf-8-*-

import bcrypt
from Crypto.Cipher import AES

class Crypter:
    
    ENCRYPT_KEY = "4843250230366837"
    ENCRYPT_IV  = "4843532393622299"

    def EncryptText(self, plaintext):
        '''Encrypt a plain text string with key & value.
        '''
        # print plaintext
        obj = AES.new(self.ENCRYPT_KEY, AES.MODE_CBC, self.ENCRYPT_IV)
        mod = len(plaintext) % 16
        if mod != 0:
            plaintext += (" " * (16 - mod))
            # print plaintext
        ciphertext = obj.encrypt(plaintext)
        # print ciphertext
        return ciphertext

    def DecryptText(self, message):
        '''Decrypt a message with key & value.
        '''
        obj = AES.new(self.ENCRYPT_KEY, AES.MODE_CBC, self.ENCRYPT_IV)
        plaintext = obj.decrypt(message)
        if len(message) % 16 != 0:
            return None
        # print plaintext
        return plaintext.strip()

    #######################################################################################################################################################################################

    def EncryptPassword(self, password):
        '''Encrypt a password using bcrypt. Return the encrypted hash value.
        '''
        hashed = bcrypt.hashpw(password, bcrypt.gensalt())
        # hashed = bcrypt.hashpw(password, bcrypt.gensalt(10))
        return hashed

    def ValidatePassword(self, inputpassword, hashedpassword):
        '''Validate a input password with the encrypted hash value. Return True if match, False if NOT match.
        '''
        ret = False
        try:
            hashed = bcrypt.hashpw(inputpassword, hashedpassword)
            ret = (hashed == hashedpassword)
        except Exception, e:
            ret = False
        
        return ret
    
    #######################################################################################################################################################################################
