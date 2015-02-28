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

"""
This module is based on the MemoryIdentityStorage class
"""
from pyndn.util import Blob
from pyndn.security.security_exception import SecurityException
from pyndn import Name
from pyndn.security.identity.identity_storage import IdentityStorage

class IotIdentityStorage(IdentityStorage):
    """
    Extend Memory Identity Storage to include the idea of default certs and keys
    """
    def __init__(self):
        super(IotIdentityStorage, self).__init__()
        # Maps identities to a list of associated keys
        self._keysForIdentity = {}

        # Maps keys to a list of associated certificates
        self._certificatesForKey = {}

        # The default identity in identityStore_, or "" if not defined.
        self._defaultIdentity = ""
        
        # The key is the keyName.toUri(). The value is the tuple 
        #  (KeyType keyType, Blob keyDer).
        self._keyStore = {}
        
        # The key is the key is the certificateName.toUri(). The value is the 
        #   encoded certificate.
        self._certificateStore = {}

    def doesIdentityExist(self, identityName):  
        """
        Check if the specified identity already exists.
        
        :param Name identityName: The identity name.
        :return: True if the identity exists, otherwise False.
        :rtype: bool
        """
        return identityName.toUri() in self._keysForIdentity
    
    def addIdentity(self, identityName):
        """
        Add a new identity. An exception will be thrown if the identity already 
        exists.

        :param Name identityName: The identity name.
        """
        identityUri = identityName.toUri()
        if identityUri in self._keysForIdentity:
            raise SecurityException("Identity already exists: " + identityUri)
  
        self._keysForIdentity[identityUri] = []
        
    def revokeIdentity(self, identityName):    
        """
        Revoke the identity. This will not purge the associated keys and certificates.
        
        :param identityName: The identity to revoke. If it is the default, there will be no replacement.
        :type identityName: Name
        :return: True if the identity was revoked, False if not.
        :rtype: bool
        """
        identityUri = identityName.toUri()
        if identityUri in self._keysForIdentity:
            self._keysForIdentity.pop(identityUri)
            return True
        return False

    def doesKeyExist(self, keyName):    
        """
        Check if the specified key already exists.
        
        :param Name keyName: The name of the key.
        :return: True if the key exists, otherwise False.
        :rtype: bool
        """
        return keyName.toUri() in self._keyStore

    def addKey(self, keyName, keyType, publicKeyDer, asDefault=False):    
        """
        Add a public key to the identity storage.
        
        :param Name keyName: The name of the public key to be added.
        :param keyType: Type of the public key to be added.
        :type keyType: int from KeyType
        :param Blob publicKeyDer: A blob of the public key DER to be added.
        :param boolean asDefault: If set, this key becomes the default for the identity
        """


        identityName = keyName.getSubName(0, keyName.size() - 1)
        identityUri = identityName.toUri()
        if not self.doesIdentityExist(identityName):
            self.addIdentity(identityName)

        if self.doesKeyExist(keyName):
            raise SecurityException("A key with the same name already exists!")
  

        keyUri = keyName.toUri()
        self._keyStore[keyUri] = (keyType, Blob(publicKeyDer))
        # add the key to the list for the identity
        if asDefault:
            self.keysforIdentity[identityUri].insert(0, keyUri)
        else:
            self._keysForIdentity[identityUri].append(keyUri)
        self._certificatesForKey[keyUri] = []

    def getKey(self, keyName):    
        """
        Get the public key DER blob from the identity storage.
        
        :param Name keyName: The name of the requested public key.
        :return: The DER Blob. If not found, return a isNull() Blob.
        :rtype: Blob
        """
        keyNameUri = keyName.toUri()
        if not (keyNameUri in self._keyStore):
            # Not found.  Silently return a null Blob.
            return Blob()
        
        (_, publicKeyDer) = self._keyStore[keyNameUri]
        return publicKeyDer

    def getKeyType(self, keyName):    
        """
        Get the KeyType of the public key with the given keyName.
        
        :param Name keyName: The name of the requested public key.
        :return: The KeyType, for example KeyType.RSA.
        :rtype: an int from KeyType
        """
        keyNameUri = keyName.toUri()
        if not (keyNameUri in self._keyStore):
            raise SecurityException(
              "Cannot get public key type because the keyName doesn't exist")
        
        (keyType, _) = self._keyStore[keyNameUri]
        return keyType


    def activateKey(self, keyName):    
        """
        Activate a key. If a key is marked as inactive, its private part will 
        not be used in packet signing.
        
        :param Name keyName: The name of the key.
        """
        raise RuntimeError(
          "MemoryIdentityStorage.activateKey is not implemented")

    def deactivateKey(self, keyName):    
        """
        Deactivate a key. If a key is marked as inactive, its private part will 
        not be used in packet signing.
        
        :param Name keyName: The name of the key.
        """
        raise RuntimeError(
         "MemoryIdentityStorage.deactivateKey is not implemented")

    def doesCertificateExist(self, certificateName):    
        """
        Check if the specified certificate already exists.
        
        :param Name certificateName: The name of the certificate.
        :return: True if the certificate exists, otherwise False.
        :rtype: bool
        """
        return certificateName.toUri() in self._certificateStore

    def addCertificate(self, certificate, asDefault=False):    
        """
        Add a certificate to the identity storage.
        
        :param IdentityCertificate certificate: The certificate to be added. 
          This makes a copy of the certificate.
        :param boolean asDefault: If set, this certificate becomes the default for the key
        """
        certificateName = certificate.getName()
        keyName = certificate.getPublicKeyName()


        certificateUri = certificateName.toUri()
        keyUri = keyName.toUri()

        if not self.doesKeyExist(keyName):
            keyInfo = certificate.getPublicKeyInfo()
            self.addKey(keyName, keyInfo.getKeyType(), keyInfo.getKeyDer())

        # Check if the certificate has already exists.
        if self.doesCertificateExist(certificateName):
            raise SecurityException("Certificate has already been installed!")

        # Check if the public key of certificate is the same as the key record.
        keyBlob = self.getKey(keyName)
        if (keyBlob.isNull() or 
              # Note: In Python, != should do a byte-by-byte comparison.
              keyBlob.toBuffer() != 
              certificate.getPublicKeyInfo().getKeyDer().toBuffer()):
            raise SecurityException(
              "Certificate does not match the public key!")
  
        # Insert the certificate.
        # wireEncode returns the cached encoding if available.
        self._certificateStore[certificateUri] = (
           certificate.wireEncode())

        # Map the key to the new certificate
        if asDefault:
            self._certificatesForKey[keyUri].insert(0, certificateUri)
        else:
            self._certificatesForKey[keyUri].append(certificateUri)


    def getCertificate(self, certificateName, allowAny = False):    
        """
        Get a certificate from the identity storage.
        
        :param Name certificateName: The name of the requested certificate.
        :param bool allowAny: (optional) If False, only a valid certificate will 
          be returned, otherwise validity is disregarded.  If omitted, 
          allowAny is False.
        :return: The requested certificate. If not found, return None.
        :rtype: Data
        """
        certificateNameUri = certificateName.toUri()
        if not (certificateNameUri in self._certificateStore):
            # Not found.  Silently return None.
            return None
  
        data = Data()
        data.wireDecode(self._certificateStore[certificateNameUri])
        return data

    #
    # Some convenience methods to assist the policy manager
    #
    def inferIdentityForName(self, someName):
        """
        Return the identity that has the longest match with the name, or empty name if no
        suitable identity can be found.
        """
        allIdentities = self._keysForIdentity.keys()

        bestName = Name()
        for identityUri in allIdentities:
            identityName = Name(identityUri)
            if identityName.match(someName):
                if identityName.size() > bestName.size():
                    bestName = identityName

        return bestName

    #
    # Get/Set Default
    #

    def getDefaultIdentity(self):    
        """
        Get the default identity.
        
        :return: The name of default identity.
        :rtype: Name
        :raises SecurityException: if the default identity is not set.
        """
        if len(self._defaultIdentity) == 0:
            raise SecurityException("The default identity is not defined")
          
        return Name(self._defaultIdentity)

    def getDefaultKeyNameForIdentity(self, identityName):    
        """
        Get the default key name for the specified identity.
        
        :param Name identityName: The identity name.
        :return: The default key name.
        :rtype: Name
        :raises SecurityException: if the default key name for the identity is 
          not set.
        """
        identityUri = identityName.toUri()
        if identityUri in self._keysForIdentity:
            # should not be any empty lists in here!
            keyList = self._keysForIdentity[identityUri]
            if len(keyList) > 0:
                return Name(keyList[0])
            else:
                raise SecurityException("No known keys for this identity.")
        else:
            raise SecurityException("Unknown identity")

    def getDefaultCertificateNameForKey(self, keyName):    
        """
        Get the default certificate name for the specified key.
        
        :param Name keyName: The key name.
        :return: The default certificate name.
        :rtype: Name
        :raises SecurityException: if the default certificate name for the key 
          name is not set.
        """
        keyUri = keyName.toUri()
        if keyUri in self._certificatesForKey:
            certList = self._certificatesForKey[keyUri]
            if len(certList) > 0:
                return Name(certList[0])
            else:
                raise SecurityException("No known certificates for this key")
        else:
            raise SecurityException("Unknown key name")

    def setDefaultIdentity(self, identityName):    
        """
        Set the default identity. If the identityName does not exist, then clear
        the default identity so that getDefaultIdentity() raises an exception.
        
        :param Name identityName: The default identity name.
        """
        identityUri = identityName.toUri()
        if identityUri in self._keysForIdentity:
            self._defaultIdentity = identityUri
        else:
            # The identity doesn't exist, so clear the default.
            self._defaultIdentity = ""

    def setDefaultKeyNameForIdentity(self, identityName, keyName):    
        """
        Set the default key name for the specified identity. The key must exist in the key store.
        
        :param Name keyName: The key name.
        :param Name identityName: (optional) The identity name to check the 
          keyName. If not set, the identity is inferred from the key name
        :raises SecurityException: if the key or identity does not exist
        """
        keyUri = keyName.toUri()
        identityUri = identityName.toUri()

        if identityUri in self._keysForIdentity:
            keyList = self._keysForIdentity[identityUri]
            if keyUri in keyList:
                keyIdx = keyList.index(keyUri)
                if keyIdx > 0:
                    # the first key is the default - nothing to do if the key is already first
                    keyList[keyIdx], keyList[0] = keyList[0], keyList[keyIdx]
            elif keyUri in self._keyStore:
                keyList.insert(0, keyUri)
            else:
                raise SecurityException("Unknown key name")
        else:
            raise SecurityException("Unknown identity name")

    def setDefaultCertificateNameForKey(self, keyName, certificateName):        
        """
        Set the default certificate name for the specified key. The certificate must exist in the certificate store.
                
        :param Name keyName: The key name.
        :param Name certificateName: The certificate name.
        :raises SecurityException: if the certificate or key does not exist
        """
        keyUri = keyName.toUri()
        certUri = certificateName.toUri()

        if keyName in self._certificatesForKey:
            certList = self._certificatesForKey[keyName]
            if certUri in certList:
                certIdx = certList.index(certUri)
                if certIdx > 0:
                    # the first key is the default - nothing to do if the key is already first
                    certList[keyIdx], certList[0] = certList[0], certList[keyIdx]
            elif certUri in self._certificateStore:
                certList.insert(0, certUri)
            else:
                raise SecurityException("Unnkown certificate name")
        else:
            raise SecurityException("Unknown key name")
