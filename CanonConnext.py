#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Dec  4 17:10:05 2018

"""

import socket

# ******** M-SEARCH******************

"""
First M-Search, seems to scan for another service
M-SEARCH * HTTP/1.1
Host:239.255.255.250:1900
ST:urn:schemas-canon-com:service:ICPO-SmartPhoneEOSSystemService:1
Man:"ssdp:discover"
MX:3
"""

"""
2nd M-Search, now that's our service
M-SEARCH * HTTP/1.1
Host: 239.255.255.250:1900
MAN: "ssdp:discover"
MX: 3
ST: urn:schemas-canon-com:service:MobileConnectedCameraService:1
"""

#************ NOTIFY***********************


"""
0th notification
NOTIFY * HTTP/1.1
Host: 239.255.255.250:1900
NT: upnp:rootdevice
NTS: ssdp:byebye
USN: uuid:7B788B31-EC1E-445A-B5EF-243274B188E5::upnp:rootdevice
"""

"""
1st notification
NOTIFY * HTTP/1.1
Host: 239.255.255.250:1900
NT: uuid:7B788B31-EC1E-445A-B5EF-243274B188E5
NTS: ssdp:byebye
USN: uuid:7B788B31-EC1E-445A-B5EF-243274B188E5
"""

"""
2nd notification
NOTIFY * HTTP/1.1
Host: 239.255.255.250:1900
NT: urn:schemas-upnp-org:device:Basic:1
NTS: ssdp:byebye
USN: uuid:7B788B31-EC1E-445A-B5EF-243274B188E5::urn:schemas-upnp-org:device:Basic:1
"""

"""
3rd notification
NOTIFY * HTTP/1.1
Host: 239.255.255.250:1900
NT: urn:schemas-canon-com:service:CameraConnectedMobileService:1
NTS: ssdp:byebye
USN: uuid:7B788B31-EC1E-445A-B5EF-243274B188E5::urn:schemas-canon-com:service:CameraConnectedMobileService:1
"""

"""
1st of another set
NOTIFY * HTTP/1.1
Host: 239.255.255.250:1900
Cache-Control: max-age=1800
Location: http://10.42.0.172:49152/MobileDevDesc.xml
NT: uuid:7B788B31-EC1E-445A-B5EF-243274B188E5
NTS: ssdp:alive
Server: Camera OS/1.0 UPnP/1.0 Android 7.1.2/Redmi 5/1.0
USN: uuid:7B788B31-EC1E-445A-B5EF-243274B188E5
"""

notifyMsg0 = \
    'NOTIFY * HTTP/1.1\r\n' \
    'Host: 239.255.255.250:1900\r\n' \
    'NT: upnp:rootdevice\r\n' \
    'NTS: ssdp:byebye\r\n' \
    'USN: uuid:7B788B31-EC1E-445A-B5EF-243274B188E5::upnp:rootdevice\r\n' \
    '\r\n'

notifyMsg1 = \
    'NOTIFY * HTTP/1.1\r\n' \
    'Host: 239.255.255.250:1900\r\n' \
    'NT: uuid:7B788B31-EC1E-445A-B5EF-243274B188E5\r\n' \
    'NTS: ssdp:byebye\r\n' \
    'USN: uuid:7B788B31-EC1E-445A-B5EF-243274B188E5\r\n' \
    '\r\n'
    
notifyMsg2 = \
    'NOTIFY * HTTP/1.1\r\n' \
    'Host: 239.255.255.250:1900\r\n' \
    'NT: urn:schemas-upnp-org:device:Basic:1\r\n' \
    'NTS: ssdp:byebye\r\n' \
    'USN: uuid:7B788B31-EC1E-445A-B5EF-243274B188E5::urn:schemas-upnp-org:device:Basic:1\r\n' \
    '\r\n'
    
notifyMsg3 = \
    'NOTIFY * HTTP/1.1\r\n' \
    'Host: 239.255.255.250:1900\r\n' \
    'NT: urn:schemas-canon-com:service:CameraConnectedMobileService:1\r\n' \
    'NTS: ssdp:byebye\r\n' \
    'USN: uuid:7B788B31-EC1E-445A-B5EF-243274B188E5::urn:schemas-canon-com:service:CameraConnectedMobileService:1\r\n' \
    '\r\n'    

mSerachMsgCanon = \
    'M-SEARCH * HTTP/1.1\r\n' \
    'Host: 239.255.255.250:1900\r\n' \
    'ST: urn:schemas-canon-com:service:MobileConnectedCameraService:1\r\n' \
    'MX: 3\r\n' \
    'MAN:"ssdp:discover"\r\n' \
    '\r\n'
    
mSerachMsgEOS = \
    'M-SEARCH * HTTP/1.1\r\n' \
    'Host: 239.255.255.250:1900\r\n' \
    'ST: urn:schemas-canon-com:service:ICPO-SmartPhoneEOSSystemService:1\r\n' \
    'MX: 3\r\n' \
    'MAN:"ssdp:discover"\r\n' \
    '\r\n'

# Set up UDP socket
s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
s.settimeout(3)


# send 4 messages0
for i in range(0,4):
    s.sendto(str.encode(notifyMsg0), ('239.255.255.250', 1900) )
    
#send 4 messages1
for i in range(0,4):
    s.sendto(str.encode(notifyMsg1), ('239.255.255.250', 1900) )
    
#send 4 messages2
for i in range(0,4):
    s.sendto(str.encode(notifyMsg2), ('239.255.255.250', 1900) )
    
#send 5 messages5
for i in range(0,5):
    s.sendto(str.encode(notifyMsg3), ('239.255.255.250', 1900) )
    
# send 2 searches of the EOS type
for i in range(0,2):
    s.sendto(str.encode(mSerachMsgEOS), ('239.255.255.250', 1900) )
    
# send 3 searches
for i in range(0,4):
    s.sendto(str.encode(mSerachMsgCanon), ('239.255.255.250', 1900) )

    
#listen for 3 seconds
try:
    while True:
        data, addr = s.recvfrom(65507)
        print(addr, data)        
except socket.timeout:
    pass
#got some data, looks good
"""
('192.168.0.1', 63476)
HTTP/1.1 200 OK\r\n
Cache-Control: max-age=1800\r\n
EXT: \r\n
Location: http://192.168.0.1:49152/CameraDevDesc.xml\r\n
Server: Camera OS/1.0 UPnP/1.0 Camera 1.0/Canon PowerShot G7 X/1.0\r\n
ST: urn:schemas-canon-com:service:MobileConnectedCameraService:1\r\n
USN: uuid:8C5A1ABA-4BE3-4A9F-9630-C11BF48437EE::urn:schemas-canon-com:service:MobileConnectedCameraService:1\r\n\r\n'
"""

#send next step of messages
    
# ------------------SECOND SET which makes us show up in the mobile devices list----------------------------------

"""
0th
NOTIFY * HTTP/1.1
Host: 239.255.255.250:1900
Cache-Control: max-age=1800
Location: http://10.42.0.172:49152/MobileDevDesc.xml
NT: upnp:rootdevice
NTS: ssdp:alive
Server: Camera OS/1.0 UPnP/1.0 Android 7.1.2/Redmi 5/1.0
USN: uuid:7B788B31-EC1E-445A-B5EF-243274B188E5::upnp:rootdevice
"""

"""
1st
NOTIFY * HTTP/1.1
Host: 239.255.255.250:1900
Cache-Control: max-age=1800
Location: http://10.42.0.172:49152/MobileDevDesc.xml
NT: uuid:7B788B31-EC1E-445A-B5EF-243274B188E5
NTS: ssdp:alive
Server: Camera OS/1.0 UPnP/1.0 Android 7.1.2/Redmi 5/1.0
USN: uuid:7B788B31-EC1E-445A-B5EF-243274B188E5
"""

"""
2nd
NOTIFY * HTTP/1.1
Host: 239.255.255.250:1900
Cache-Control: max-age=1800
Location: http://10.42.0.172:49152/MobileDevDesc.xml
NT: urn:schemas-upnp-org:device:Basic:1
NTS: ssdp:alive
Server: Camera OS/1.0 UPnP/1.0 Android 7.1.2/Redmi 5/1.0
USN: uuid:7B788B31-EC1E-445A-B5EF-243274B188E5::urn:schemas-upnp-org:device:Basic:1
"""

"""
3rd
NOTIFY * HTTP/1.1
Host: 239.255.255.250:1900
Cache-Control: max-age=1800
Location: http://10.42.0.172:49152/MobileDevDesc.xml
NT: urn:schemas-canon-com:service:CameraConnectedMobileService:1
NTS: ssdp:alive
Server: Camera OS/1.0 UPnP/1.0 Android 7.1.2/Redmi 5/1.0
USN: uuid:7B788B31-EC1E-445A-B5EF-243274B188E5::urn:schemas-canon-com:service:CameraConnectedMobileService:1
"""

notifyMsg0 = \
    'NOTIFY * HTTP/1.1\r\n' \
    'Host: 239.255.255.250:1900\r\n' \
    'Cache-Control: max-age=1800\r\n' \
    'Location: http://10.42.0.172:49152/MobileDevDesc.xml' \
    'NT: upnp:rootdevice\r\n' \
    'NTS: ssdp:alive\r\n' \
    'Server: Camera OS/1.0 UPnP/1.0 Android 7.1.2/Redmi 5/1.0'\
    'USN: uuid:7B788B31-EC1E-445A-B5EF-243274B188E5::upnp:rootdevice\r\n' \
    '\r\n'
    
notifyMsg1 = \
    'NOTIFY * HTTP/1.1\r\n' \
    'Host: 239.255.255.250:1900\r\n' \
    'Cache-Control: max-age=1800\r\n' \
    'Location: http://10.42.0.172:49152/MobileDevDesc.xml' \
    'NT: upnp:rootdevice\r\n' \
    'NTS: ssdp:alive\r\n' \
    'Server: Camera OS/1.0 UPnP/1.0 Android 7.1.2/Redmi 5/1.0'\
    'USN: uuid:7B788B31-EC1E-445A-B5EF-243274B188E5::upnp:rootdevice\r\n' \
    '\r\n'
    
notifyMsg2 = \
    'NOTIFY * HTTP/1.1\r\n' \
    'Host: 239.255.255.250:1900\r\n' \
    'Cache-Control: max-age=1800\r\n' \
    'Location: http://10.42.0.172:49152/MobileDevDesc.xml' \
    'NT: upnp:rootdevice\r\n' \
    'NTS: ssdp:alive\r\n' \
    'Server: Camera OS/1.0 UPnP/1.0 Android 7.1.2/Redmi 5/1.0'\
    'USN: uuid:7B788B31-EC1E-445A-B5EF-243274B188E5::upnp:rootdevice\r\n' \
    '\r\n'
    
notifyMsg3 = \
    'NOTIFY * HTTP/1.1\r\n' \
    'Host: 239.255.255.250:1900\r\n' \
    'Cache-Control: max-age=1800\r\n' \
    'Location: http://10.42.0.172:49152/MobileDevDesc.xml' \
    'NT: upnp:rootdevice\r\n' \
    'NTS: ssdp:alive\r\n' \
    'Server: Camera OS/1.0 UPnP/1.0 Android 7.1.2/Redmi 5/1.0'\
    'USN: uuid:7B788B31-EC1E-445A-B5EF-243274B188E5::upnp:rootdevice\r\n' \
    '\r\n'