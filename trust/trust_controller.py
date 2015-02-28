
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

from pyndn import Name, Data, Interest, ThreadsafeFace

from pyndn.security.certificate import IdentityCertificate, Certificate
from pyndn.security import KeyChain
from pyndn.security.identity import IdentityManager
from pyndn.security.security_exception import SecurityException

from pyndn.encoding import ProtobufTlv

from iot_policy_manager import IotPolicyManager
from iot_identity_storage import IotIdentityStorage


from new_environment_pb2 import NewEnvironmentCommandMessage
from install_certificate_pb2 import InstallCertificateCommandMessage

import base64
import trollius as asyncio
import time
import struct

def findIdxOfNameComponent(name, target):
    loc = -1
    for i in range(name.size()):
        if name.get(i).toEscapedString() == target:
            loc = i
            break
    return loc

"""
The IotTrustController class acts as the publisher of identity certificates for a
group of devices/names. The controller sends a command interest to invite devices
to join its trust group. They must respond with an identity certificate that will 
be signed by the IotTrust controller and published under a new name. The IotTrustController
will then inform the devices of the name of their new certificates. These devices
should download the certificates to ensure they are correct, and acknowledge the
information, using the key and certificate name on the Data signature.
"""

class IotTrustController(object):
    def __init__(self):
        self._identityStorage = IotIdentityStorage()
        self._identityManager = IdentityManager(self._identityStorage)
        self._policyManager = IotPolicyManager(self._identityStorage)
        self._keychain = KeyChain(self._identityManager, self._policyManager)

        #TODO: put this in a config file
        self._certPrefix = Name("/ndn/ucla.edu/sculptures/ai_bus/controller/AUTH")
        # the face we use to publish certs
        self.certificateFace = None

        topIdentity = Name("/ndn/ucla.edu/sculptures/ai_bus/controller")

        rootCert = self.loadIdentityCertificateFromFile('trust_root.cert')
        self._policyManager.installRootCertificate(rootCert)
        self._identityStorage.setDefaultIdentity(topIdentity)
        self._defaultCertName = self._keychain.getDefaultCertificateName()

    @staticmethod
    def loadIdentityCertificateFromFile(certFilename):
        # the file should contain a wireEncode()d IdentityCertificate
        with open(certFilename, 'r') as certStream:
            encodedCertLines = certStream.readlines()
            encodedCert = ''.join(encodedCertLines)
            certData = bytearray(base64.b64decode(encodedCert))
            cert = IdentityCertificate()
            cert.wireDecode(certData)
            return cert

    def generateCertificateFromRequest(self, csr, shortName):
        """
        The signed certificate is assigned a new name for distibution by the trust controller
        We replace everything before /KEY/ with /<_certPrefix>/<shortName>/
        We also adjust the timestamp

        We make a copy of the CSR
        """
        newCert = IdentityCertificate(csr)

        keyIdx = findIdxOfNameComponent(newCert.getName(), "KEY")
        nameLen = newCert.getName().size()

        newCertName = Name(self._certPrefix).append(shortName).append(newCert.getName().getSubName(keyIdx, nameLen-keyIdx-1))

        timestamp = (time.time())
        newCertName.append(Name.Component(struct.pack(">l", timestamp)))
        newCert.setName(newCertName)

        self._keychain.sign(newCert, self._defaultCertName)

        return newCert

    def generateEnvironmentInvitationCommand(self, devicePrefix):
        interestName = Name(devicePrefix).append("new-environment")
        commandParams = NewEnvironmentCommandMessage()

        #TODO: add environment name
        commandParams.command.environmentName.components.append("")

        interestName.append(ProtobufTlv.encode(commandParams))
        return Interest(interestName)



    def generateInstallCertificateCommand(self, devicePrefix, certificateName):
        interestName = Name(devicePrefix).append("install-certificate")
        commandParams = InstallCertificateCommandMessage()
        
        for i in range(certificateName.size()):
            commandParams.command.certificateName.components.append(certificateName.get(i).toEscapedString())

        interestName.append(ProtobufTlv.encode(commandParams))
        return Interest(interestName)


    def inviteToEnvironment(self, devicePrefix):
        """
        Send a command interest inviting another device to join the trust environment
        It should rspond with a Certificate Signing Request
        """
        

def main():
    controller = IotTrustController()
    light_request = IotTrustController.loadIdentityCertificateFromFile('lights_request.cert')
    print light_request

    signedCert = controller.generateCertificateFromRequest(light_request, Name("lights"))
    print signedCert

    installCommand = controller.generateInstallCertificateCommand(Name("/ndn/ucla.edu/blablabla/"), signedCert.getName())
    print installCommand.toUri()


if __name__ == '__main__':
    main()
