
# -*- Mode:python; c-file-style:"gnu"; indent-tabs-mode:nil -*- */
#
# Copyright (C) 2014 Regents of the University of California.
# Author: Adeola Bannis <thecodemaiden@gmail.com>
# 
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
# A copy of the GNU General Public License is in the file COPYING.

from Crypto.Cipher import AES
from Crypto.Hash import SHA256
from getpass import getpass
from base64 import b64encode, b64decode
import os

# User intervention is required 

def getKeyDataFromFile(filename, prompt="Passphrase: "):
    keyData = bytearray()

    with open(filename, 'rb') as stream:
        encryptedKey = stream.read()
        iv = str(encryptedKey[:16])
        passphrase = getpass(prompt)
        hasher = SHA256.new(passphrase)
        cipher = AES.new(hasher.digest(), AES.MODE_CBC, IV=iv)
        for i in range(16, len(encryptedKey), 16):
            chunk = cipher.decrypt(encryptedKey[i:i+16])
            keyData.extend(chunk)

        keyData = b64decode(keyData)

    return keyData

def storeKeyDataToFile(filename, keyBits, prompt="Passphrase: "):
    encryptedKey = bytearray()
    with open(filename, 'wb') as stream:
        iv = os.urandom(16)
        passphrase = getpass(prompt)
        hasher = SHA256.new(passphrase)
        cipher = AES.new(hasher.digest(), AES.MODE_CBC, IV=iv)
        encryptedKey.extend(iv)

        keyStr = b64encode(keyBits)
        for i in range(0, len(keyStr), 16):
            chunk = keyStr[i:i+16]
            if len(chunk) < 16:
                chunk += ' '*(16 - len(chunk))
            encryptedKey.extend(cipher.encrypt(chunk))

        stream.write(encryptedKey)

if __name__ == "__main__":
    testKey = "This is a story about a key that needed strong encryption."
    testFileName = "test.pri"

    storePrivateKeyToFile(testFileName, testKey)
    print getPrivateKeyFromFile(testFileName)
