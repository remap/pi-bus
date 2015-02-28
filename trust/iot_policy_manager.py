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


from pyndn.security.policy import SelfVerifyPolicyManager, ValidationRequest
from pyndn.security.certificate import Certificate
from pyndn.security.identity import PublicKey
from pyndn import Name, Data, Interest


"""
This module implements a simple hierarchical trust model that uses certificate
data to determine whether another signature/name can be trusted.

The policy manager expects to operate within an _environment_, which must be present
as an Organization attribute in the Subject Description fields of a certificate. All
data/interests signed with a certificate in this environment will be trusted.

If there is no environment set, any command interest to establish an environment will be trusted, and the sender will be the top authority of thisnew environment.

There is a root name and public key which must be the top authority in the environment
for the certificate to be trusted.

The policy manager also maintains a cache of Name prefixes->public key bits for authorized
names.

"""


class IotPolicyManager(SelfVerifyPolicyManager):
    def __init__(self, identityStorage, environmentName = None):
        super(IotPolicyManager, self).__init__(identityStorage)
        self._environmentName = environmentName
        self._trustRootIdentity = None

    def skipVerifyAndTrust(self, data):
        return self._trustRootIdentity is not None

    def requireVerify(self, data):
        return self._trustRootIdentity is None

    def inferSigningIdentity(self, dataName):
        try:
            return self._identityStorage.inferIdentityForName(dataName)
        except AttributeError:
            return Name()

    #def checkVerificationPolicy(self, data, stepCount, onVerified, 
        #TODO: hierarchical trust!

    def installRootCertificate(self, certificate):
        """
        Install the certificate and set the identity, key and certificate within to be the trust
        root's credentials.

        :param certData: The downloaded root certificate
        :type certData: IdentityCertificate
        """
        # extract the identity name from the cert name (everything before 'KEY')
        idx = -1
        certName = certificate.getName()
        for i in range(certName.size()):
            if certName.get(i).toEscapedString() == 'KEY':
                idx = i
                break

        identityName = certName.getPrefix(idx)

        if not self._identityStorage.doesCertificateExist(certName):
            self._identityStorage.addCertificate(certificate)

        self._trustRootIdentity = identityName

    def setEnvironmentName(self, name):
        self._environmentName = name

    def getEnvironmentName(self):
        return self._environmentName
