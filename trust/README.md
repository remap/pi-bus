This holds a simple trust model implementation (not bootstrapped). There is an application domain: all certificates issued within this domain are trusted on all names in the domain. The trust root knows (must be told) the names of devices that belong in the domain.  

 PHASE 1: Establishing trust
============================

To establish the domain, the trust root generates a public/private key pair for the domain,and generates its certificate. It then sends a command interest to each device:
        /<device name>/new-environment/<parameters>
        Parameters:
            - environment name
        
The devices receive the command interest, download the certificate from the KeyLocator of the data, and verify the signature with the controller's public key. If it is acceptable and they want to join the environment (always for my implementation), they generate a key pair for the environment and reply with the public key.  

The controller then generates certs for each device, and issues another command interest to request installation:
        /<device name>/install-certificate/<parameters>
        Parameters:
            - certificate network name

The devices download the certificate and verify that it contains the correct device name and environment name, and that it was signed by the same entity that initiated the trust environment. The device responds with success or failure according to the validity of the new certificate.  


 PHASE 2: First interactions
============================

When a signed interest or data packet is first received, the receiver must:
    1. download the certificate given in KeyLocator of Signature
    2. check environment name and issuer certificate name
    3. verify certificate was signed with controller's private
    4. verify the data/interest with key in downloaded certificate
If everything checks out, the receiver will cache the public key bits together with the name of the device. All data/interests under this prefix will be authorized.  


 Certificate Fields
======================

For my personal reference, the certificate will contain:


Subject Description
-------------------
    2.5.4.5:    NDN Name prefix for certificate owner
    2.5.4.10:   Environment name
    
Certificate Extension
---------------------
    This is needed mainly to establish a more complex hierarchical model later.

    2.5.29.18:  Issuer's certificate name

