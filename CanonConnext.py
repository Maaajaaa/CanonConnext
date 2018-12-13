#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Dec  4 17:10:05 2018

"""

import socket
import netifaces as ni
import urllib3
import re
import xml.etree.cElementTree as ET

ip = ni.ifaddresses('wlp3s0')[ni.AF_INET][0]['addr']
print(ip)
host_port = '49152'

# DEVICE SETTINGS

#TODO: create unique uuid when name changes, f.e. constant+name's MD5 or so

uuid = '7B788B31-EC1E-445A-B5EF-243274B188F6'
#os and name should not contain some characters like /
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
    


#request and read the CameraDevDesc.xml
#url = 'http://192.168.0.1:49152/CameraDevDesc.xml'

if gotData:
    url = re.search("(?P<url>https?://[^\s]+)", data.decode("utf-8")).group("url")
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
  
#Craft MobileDevDesc.xml
    
root = ET.Element('root', xmlns="urn:schemas-upnp-org:device-1-0")
specVersion = ET.SubElement(root, 'specVersion')
ET.SubElement(specVersion, 'major').text = '1'
ET.SubElement(specVersion, 'minor').text = '0'
#IP-address and port for ongoing conversation (this would be another way of hacking the system, but the camera accepts requests from any device in the network once it is "connected" to a device anyway)
urlbase = ET.SubElement(root, 'URLBase').text = 'http://' + ip + ':' + host_port + '/'
device = ET.SubElement(root, 'device')
ET.SubElement(device, 'deviceType').text = 'urn:schemas-upnp-org:device:Basic:1'
ET.SubElement(device, 'friendlyName').text = friendly_name
#I know this sounds wrong, but that's what the Canon App does as well, so whatever
ET.SubElement(device, 'manufacturer').text = 'CANON INC.'
ET.SubElement(device, 'manufacturerURL').text = 'http://www.canon.com/'
ET.SubElement(device, 'modelDescription').text = 'Canon Mobile Simulator'
ET.SubElement(device, 'modelName').text = os + '/' + friendly_name
ET.SubElement(device, 'UDN').text = 'uuid:' + uuid
serviceList = ET.SubElement(device, 'serviceList')
service = ET.SubElement(serviceList, 'service')
ET.SubElement(service, 'serviceType').text = 'urn:schemas-canon-com:service:CameraConnectedMobileService:1'
ET.SubElement(service, 'serviceId').text = 'urn:schemas-canon-com:serviceId:CameraConnectedMobile'
ET.SubElement(service, 'SCPDURL').text = 'desc/CameraConnectedMobile.xml'
ET.SubElement(service, 'controlURL').text = 'CameraConnectedMobile/'
ET.SubElement(service, 'eventSubURL').text = ' '
nsElement1 = ET.SubElement(service, 'ns:X_SCPDURL')
nsElement1.text = 'desc_iml/CameraConnectedMobile.xml'
nsElement1.set('xmlns:ns', "urn:schemas-canon-com:schema-imink")
nsElement2 = ET.SubElement(service, 'ns:X_ExtActionVer')
nsElement2.text = '1.0'
nsElement2.set('xmlns:ns', "urn:schemas-canon-com:schema-imink")
#meaning of X_VendorExtVer unkown to me
nsElement3 = ET.SubElement(service, 'ns:X_VendorExtVer')
nsElement3.text = '1-1502.0.0.0'
nsElement3.set('xmlns:ns', "urn:schemas-canon-com:schema-imink")
ET.SubElement(device, 'presentationURL').text = '/'

tree = ET.ElementTree(root)
tree.write("serverFiles/MobileDevDesc.xml")

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
for T in range(3):
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
    
#get MobileConnectedCamera.xml
r = http.request('GET', 'http://' + re.search("[0-9.]+", url).group() + ':49152/desc_iml/MobileConnectedCamera.xml?uuid=' + uuid, preload_content=False)
while True:
    MobileConnectedCamera = r.read()
    if not MobileConnectedCamera:
        break
    print("\n\nGot MobileConnectedCamera.xml:\n")
    print(MobileConnectedCamera)
    print("\n\n")
r.release_conn()