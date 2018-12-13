#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Dec 12 17:08:05 2018

@author: mattis
"""


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
Location: http://192.168.0.2:49152/MobileDevDesc.xml
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
Location: http://192.168.0.2:49152/MobileDevDesc.xml
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
Location: http://192.168.0.2:49152/MobileDevDesc.xml
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
Location: http://192.168.0.2:49152/MobileDevDesc.xml
NT: urn:schemas-canon-com:service:CameraConnectedMobileService:1
NTS: ssdp:alive
Server: Camera OS/1.0 UPnP/1.0 Android 7.1.2/Redmi 5/1.0
USN: uuid:7B788B31-EC1E-445A-B5EF-243274B188E5::urn:schemas-canon-com:service:CameraConnectedMobileService:1
"""