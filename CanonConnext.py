#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Dec  4 17:10:05 2018

"""

import socket
import netifaces as ni
import urllib3
import re

ip = ni.ifaddresses('wlp3s0')[ni.AF_INET][0]['addr']
print(ip)
host_port = '49152'

# DEVICE SETTINGS

uuid = '7B788B31-EC1E-445A-B5EF-243274B188E6'
os = 'Debian 9'
friendly_name = 'Cannon Connext'

# ------------SSDP NOTIFY Messages--------------------

notifyBase = \
    'NOTIFY * HTTP/1.1\r\n' \
    'Host: 239.255.255.250:1900\r\n' \
    'NTS: ssdp:byebye\r\n' 
    
notifyExtension = ['' for x in range(4)]
    
notifyExtension[0] = \
    'NT: upnp:rootdevice\r\n' \
    'USN: uuid:' + uuid + '::upnp:rootdevice\r\n' \
    '\r\n'

notifyExtension[1] = \
    'NT: uuid:7B788B31-EC1E-445A-B5EF-243274B188E5\r\n' \
    'USN: uuid:' + uuid + '\r\n' \
    '\r\n'
    
notifyExtension[2] = \
    'NT: urn:schemas-upnp-org:device:Basic:1\r\n' \
    'USN: uuid:' + uuid + '::urn:schemas-upnp-org:device:Basic:1\r\n' \
    '\r\n'
    
notifyExtension[3] = \
    'NT: urn:schemas-canon-com:service:CameraConnectedMobileService:1\r\n' \
    'USN: uuid:' + uuid + '::urn:schemas-canon-com:service:CameraConnectedMobileService:1\r\n' \
    '\r\n'
    
# -------------SSDP M-SEARCH Messages----------------

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

for i in range(4):
    # send 4 messages
    for j in range(4):
        s.sendto(str.encode(notifyBase + notifyExtension[i]), ('239.255.255.250', 1900) )
    
# send 3 searches of each type
for i in range(3):
    s.sendto(str.encode(mSerachMsgEOS), ('239.255.255.250', 1900) )
    s.sendto(str.encode(mSerachMsgCanon), ('239.255.255.250', 1900) )

gotData=0
    
#listen for 3 seconds
try:
    while True:
        data, addr = s.recvfrom(65507)
        if data!="":
            gotData=1
        print(addr, data)
except socket.timeout:
    pass

#this is a bad way but should do it for now, will cause issues when other Upnp devices are in the same network
    
url = re.search("(?P<url>https?://[^\s]+)", data.decode("utf-8")).group("url")

#request and read the CameraDevDesc.xml
#url = 'http://192.168.0.1:49152/CameraDevDesc.xml'

if gotData:
    http = urllib3.PoolManager()
    r = http.request('GET', url, preload_content=False)
    
    while True:
        CameraDevDesc = r.read()
        if not CameraDevDesc:
            break
        print("\n\nGot CameraDevDesc.xml:\n")
        print(CameraDevDesc)
        print("\n\n")
    r.release_conn()

#proper introduction

notifyBase =  \
    'NOTIFY * HTTP/1.1\r\n' \
    'Host: 239.255.255.250:1900\r\n' \
    'Cache-Control: max-age=1800\r\n' \
    'Location: http://'+ ip + ':' + host_port + '/MobileDevDesc.xml\r\n' \
    'Server: Camera OS/1.0 UPnP/1.0 ' + os + '/' + friendly_name + '/1.0\r\n'\

notifyExtension[0] = \
    'NT: upnp:rootdevice\r\n' \
    'NTS: ssdp:alive\r\n' \
    'USN: uuid:' + uuid + '::upnp:rootdevice\r\n' \
    '\r\n'
    
notifyExtension[1] = \
    'NT: uuid:' + uuid + '\r\n' \
    'NTS: ssdp:alive\r\n' \
    'USN: uuid:' + uuid + '\r\n' \
    '\r\n'
    
notifyExtension[2] = \
    'NT: urn:schemas-upnp-org:device:Basic:1\r\n' \
    'NTS: ssdp:alive\r\n' \
    'USN: uuid:' + uuid + '::urn:schemas-upnp-org:device:Basic:1\r\n' \
    '\r\n'
    
notifyExtension[3] = \
    'NT: urn:schemas-canon-com:service:CameraConnectedMobileService:1\r\n' \
    'NTS: ssdp:alive\r\n' \
    'USN: uuid:' + uuid + '::urn:schemas-canon-com:service:CameraConnectedMobileService:1\r\n' \
    '\r\n'
    
#poorly implemented timeout
for T in range(20):
    # send 3 m-searches of each type
    for i in range(3):
        s.sendto(str.encode(mSerachMsgEOS), ('239.255.255.250', 1900) )
        s.sendto(str.encode(mSerachMsgCanon), ('239.255.255.250', 1900) )
        
    for i in range(4):
        # send 4 messages
        for j in range(4):
            s.sendto(str.encode(notifyBase + notifyExtension[i]), ('239.255.255.250', 1900) )
    
    #listen for 3 seconds
    try:
        while True:
            data, addr = s.recvfrom(65507)
            print(addr, data)        
    except socket.timeout:
        pass