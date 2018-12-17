#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Dec  4 17:10:05 2018

"""

import socket
import netifaces as ni
import urllib3
from io import BytesIO
from requests import Request, Session, get
from time import sleep
import re
import xml.etree.cElementTree as ET
from http.server import HTTPServer, SimpleHTTPRequestHandler, HTTPStatus
import os
import threading
from bitarray import bitarray

runSSDPOnAndOn = True
connectedToCamera = False
debug = False

cameraIP = '192.168.0.106'
    
# HTTPRequestHandler class
class iminkRequestHandler(SimpleHTTPRequestHandler):  
    gotAskedForCCM = False
    server_version = 'OS/Version UPnP/1.0'
    sys_version = 'UPeNd/1.5 cHttpdHandlerSock'

    def do_POST(self):
        """Methode to handle POST requests"""
        content_length = int(self.headers['Content-Length'])
        body = self.rfile.read(content_length)
        bodyStr = body.decode('utf-8')
        requestKnown = False
        
        #Detecting Run status request and answering with statusReplyRun.xml:
        if '<Status>Run</Status>' in bodyStr:
            requestKnown = True
            #TODO: put this in a try loop
            with open('GETreplies/statusRunReply.xml') as replyFile:
                    replyStr = replyFile.read()  
                    self.sendResponse(replyStr)      
            if debug:print('Status Run request handled')
            return
            
        #Acknowledge CapabilityInfo
        if '<Pull_Operating>' in bodyStr:
            requestKnown = True
            with open('GETreplies/null.xml') as replyFile:
                    replyStr = replyFile.read()
                    self.sendResponse(replyStr)
            if debug:print('CapabilityInfo acknowledged')
            return
            
        #Acknowledge CameraInfo
        if '<CardProtect>' in bodyStr:
            requestKnown = True
            with open('GETreplies/null.xml') as replyFile:
                    replyStr = replyFile.read()
                    self.sendResponse(replyStr)      
            if debug:print('CameraInfo acknowledged')
            return
        
        #Acknowledge NCFData
        if '<AARData>' in bodyStr:
            requestKnown = True
            with open('GETreplies/null.xml') as replyFile:
                    replyStr = replyFile.read()
                    self.sendResponse(replyStr)      
            if debug:print('NFCData acknowledged')
            return
        
        #Detect Status Stop
        if '<Status>Stop</Status>' in bodyStr:
            requestKnown = True
            #TODO: put this in a try loop
            with open('GETreplies/statusStopReply.xml') as replyFile:
                    replyStr = replyFile.read()  
                    self.sendResponse(replyStr)                     
            print("Status Stop request handled, in other words: We're in")
            global connectedToCamera
            connectedToCamera = True   
            return
        
        if not requestKnown:
            response = BytesIO()
            self.send_response(200)
            self.end_headers()
            response.write(body)
            print('got unknown POST request')
            print('header')
            print(self.headers)
            print('body: ' + bodyStr)
            self.wfile.write(response.getvalue())
        
    def sendResponse(self, bodyStr):
        """Takes a string and sends it as a reponse to a GET-request with apporpriate headers"""
        #header
        content_length = len(str.encode(bodyStr))
        if content_length is 0:
            self.send_response_only(HTTPStatus.OK)            
            self.send_header("Content-Length", content_length)
            self.send_header('Server', self.version_string())
            self.send_header('Date', self.date_time_string())
        else:
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Length", content_length)
        if content_length is not 0:
            self.send_header("Content-Type", 'text/xml ; charset=utf-8')
        self.end_headers()
        response = BytesIO()
        response.write(str.encode(bodyStr))
        self.wfile.write(response.getvalue())
        
    def do_GET(self):
        """Serve a GET request and send a request RIGHT after we get asked for CameraConnectedMobile.xml the first time"""
        f = self.send_head()
        if f:
            try:
                self.copyfile(f, self.wfile)
                fname = os.path.basename(f.name)
                if self.gotAskedForCCM is False and 'CameraConnectedMobile.xml' in fname:
                    self.gotAskedForCCM = True
            finally:
                f.close()
                
def imink_response_sever():
    print('starting server in separate thread')
    #change dir to serverFiles
    server_address = ('', 8615)
    server = HTTPServer(server_address, iminkRequestHandler)
    server.serve_forever()

# HTTPRequestHandler class
class SSDP_RequestHandler(SimpleHTTPRequestHandler):  
    gotAskedForCCM = False
    def do_GET(self):
        """Serve a GET request and send a GET request RIGHT after we get asked for CameraConnectedMobile.xml the first time to skip long waits"""
        f = self.send_head()
        if f:
            try:
                self.copyfile(f, self.wfile)
                fname = os.path.basename(f.name)
                if self.gotAskedForCCM is False and 'CameraConnectedMobile.xml' in fname:
                    self.gotAskedForCCM = True
                    global runSSDPOnAndOn
                    runSSDPOnAndOn = False
                    http = urllib3.PoolManager()
                    r = http.request('GET', 'http://' + cameraIP + ':49152/desc_iml/MobileConnectedCamera.xml?uuid=7B788B31-EC1E-445A-B5EF-243274B188F6', preload_content=False)
                    while True:
                        MobileConnectedCamera = r.read()
                        if not MobileConnectedCamera:
                            break
                        if debug:
                            print("\n\nGot MobileConnectedCamera.xml:\n")
                            print(MobileConnectedCamera)
                            print("\n\n")
                    r.release_conn()
            finally:
                f.close()
                
def start_ssdp_response_server():
    print('starting server in separate thread')
    #change dir to serverFiles
    server_address = ('', 49152)
    server = HTTPServer(server_address, SSDP_RequestHandler)
    server.serve_forever()
    

ip = ni.ifaddresses('wlp3s0')[ni.AF_INET][0]['addr']
print(ip)
host_port = '49152'

# DEVICE SETTINGS

#TODO: create unique uuid when name changes, f.e. constant+name's MD5 or so
uuid = '7B788B31-EC1E-445A-B5EF-243274B188F6'

#os and name should not contain /
system = 'Debian 9'
friendly_name = 'Cannon Connext'

# ------------SSDP NOTIFY Messages--------------------
notifyBase = ''
notifyExtension = ['' for x in range(4)]

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

gotData = 0
data = ''

def defineNotifications(stage):
    """set notifyBase and notifyExtension to the right stage"""
    
    global notifyBase, notifyExtension
    
    if stage is 1:
        notifyBase = \
        'NOTIFY * HTTP/1.1\r\n' \
        'Host: 239.255.255.250:1900\r\n' \
        'NTS: ssdp:byebye\r\n' 
        
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
            
    if stage is 2:
        #proper introduction
        notifyBase =  \
            'NOTIFY * HTTP/1.1\r\n' \
            'Host: 239.255.255.250:1900\r\n' \
            'Cache-Control: max-age=1800\r\n' \
            'Location: http://'+ ip + ':' + host_port + '/MobileDevDesc.xml\r\n' \
            'Server: Camera OS/1.0 UPnP/1.0 ' + system + '/' + friendly_name + '/1.0\r\n'\
        
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
        
def sendNotify(stage):
    """"SEND NOTIFY messsage of given stage"""
    
    global gotData, data
    
    defineNotifications(stage)    
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
        
    #listen for 3 seconds    
    #this is a bad way but should do it for now, will cause issues when other Upnp devices are in the same network
    try:
        while True:
            data, addr = s.recvfrom(65507)
            if data!="":
                gotData=1
            if debug: print(addr, data)
    except socket.timeout:
        pass

    
def getCameraDevDesc():
    #request and read the CameraDevDesc.xml
    
    global gotData, data
    http = urllib3.PoolManager()
    if gotData:
        url = re.search("(?P<url>https?://[^\s]+)", data.decode("utf-8")).group("url")
        r = http.request('GET', url, preload_content=False)
        
        while True:
            CameraDevDesc = r.read()
            if not CameraDevDesc:
                break
            if debug:
                print("\n\nGot CameraDevDesc.xml:\n")
                print(CameraDevDesc)
                print("\n\n")
        r.release_conn()
        
def makeMobileDevDesc():
    #make MobileDevDesc.xml, modifying get's messy because of the partial namespace  
    root = ET.Element('root', xmlns="urn:schemas-upnp-org:device-1-0")
    specVersion = ET.SubElement(root, 'specVersion')
    ET.SubElement(specVersion, 'major').text = '1'
    ET.SubElement(specVersion, 'minor').text = '0'
    #IP-address and port for ongoing conversation (this would be another way of hacking the system, but the camera accepts requests from any device in the network once it is "connected" to a device anyway)
    ET.SubElement(root, 'URLBase').text = 'http://' + ip + ':' + host_port + '/'
    device = ET.SubElement(root, 'device')
    ET.SubElement(device, 'deviceType').text = 'urn:schemas-upnp-org:device:Basic:1'
    ET.SubElement(device, 'friendlyName').text = friendly_name
    #I know this sounds wrong, but that's what the Canon App does as well, so whatever
    ET.SubElement(device, 'manufacturer').text = 'CANON INC.'
    ET.SubElement(device, 'manufacturerURL').text = 'http://www.canon.com/'
    ET.SubElement(device, 'modelDescription').text = 'Canon Mobile Simulator'
    ET.SubElement(device, 'modelName').text = system + '/' + friendly_name
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
    tree.write("MobileDevDesc.xml")
    
def removeXMLNamespace(xmlstring):
    xmlstring = re.sub(r'\sxmlns="[^"]+"', '', xmlstring, count=1)
    return xmlstring

def extractThumbFromExifHeader(exitfbytes):
    """
    Extract JPEG thumbnail from Exif header, this method is pretty hacky and 
    only works well in THIS case because they're all the same
    """
    exifbits = bitarray()
    exifbits.frombyes(exitfbytes)
    
    ffd8 = bitarray()
    ffd8.frombytes(b'\xFF\xD8')
    
    ffd9 = bitarray()
    ffd9.frombytes(b'\xFF\xD9')
    
    ffd8s = exifbits.search(ffd8) 
    ffd9s = exifbits.search(ffd9)
    
    print(ffd8s)
    
    print(ffd9s)
    #cut from 3rd occurence of ffd8 to ffd9 but include ffd9 which is 16 BITS long
    exifbits = exifbits[ffd8s[2]:ffd9s[0]+16]
    
    return exifbits.tobytes()

# start server treads
t = threading.Thread(target=start_ssdp_response_server)
t.start()

t2 = threading.Thread(target=imink_response_sever)
t2.start()

while not connectedToCamera:
    if runSSDPOnAndOn:
        sendNotify(stage=1)
        if gotData:
            getCameraDevDesc()
            makeMobileDevDesc()
            sendNotify(stage=2)
            gotData=False
    else:
        sleep(0.01)
        
#We're in like Flinn
with open('POSTrequests/statusRunRequest.xml') as requestFile:
                              
    s = Session()
    
    req = Request('POST', 'http://' + cameraIP + ':8615/MobileConnectedCamera/UsecaseStatus?Name=ObjectPull&MajorVersion=1&MinorVersion=0', data=str.encode(requestFile.read()))
    prepped = req.prepare()    
    prepped.headers['Content-Type'] = 'text/xml ; charset=utf-8'        
    resp = s.send(prepped)
    print(resp.status_code, resp.content)
    
    req = Request('GET', 'http://' + cameraIP + ':8615/MobileConnectedCamera/ObjIDList?StartIndex=1&MaxNum=1&ObjType=ALL')
    prepped = req.prepare()    
    prepped.headers['Content-Type'] = 'text/xml ; charset=utf-8'
    resp = s.send(prepped)
    print(resp.status_code, resp.content)
    if resp.status_code is 200:
        #removing the namespace akes parsing much simpler
        resultSet = ET.fromstring(removeXMLNamespace(resp.content.decode("utf-8")) )
        #print(resultSet.tag)
        totalNumOfItemsOnCamera = int(resultSet.find('TotalNum').text)
        tree = ET.ElementTree(resultSet)
        tree.write('myLittleResultSet.xml')
        
        objID1 = resultSet.find('ObjIDList-1')
        #get IDs, types and groups
        objectsIndexed = 0
        #make an XML to save the properties
        camerasObjects = ET.Element('camerasObects')
        while objectsIndexed < totalNumOfItemsOnCamera:
            #http://192.168.0.106:8615/MobileConnectedCamera/GroupedObjIDList?StartIndex=1&ObjType=ALL&GroupType=1
            #meaning of GroupType is unlear to me
            r = get('http://' + cameraIP + ':8615/MobileConnectedCamera/GroupedObjIDList?StartIndex=' + str(objectsIndexed +1) + '&MaxNum=100&ObjType=ALL&GroupType=1')
            resultSet = ET.fromstring(removeXMLNamespace(r.text) )
            #print("got:" + r.text)
            for listID in range(1,int(resultSet.find('ListCount').text) + 1):       
                listIDStr = str(listID)
                ET.SubElement(camerasObjects, 'Obj', {
                        'myID':str(objectsIndexed), 
                        'objID':resultSet.find('ObjIDList-' + listIDStr).text, 
                        'objType':resultSet.find('ObjTypeList-' + listIDStr).text, 
                        'groupNr':resultSet.find('GroupedNumList-' + listIDStr).text})
                objectsIndexed += 1
            print('Got soo many Elements:' + str(objectsIndexed))   
            
        #save xml
        tree = ET.ElementTree(camerasObjects)
        tree.write('myBigResultSet.xml')
        
        #fetch EXIF-header which contains a small thumb, remember the thumb is designed to show up on small medium-dense camera screen not a 4k tablet
        #10.42.0.179:8615/MobileConnectedCamera/ObjParsingExifHeaderList?ListNum=1&ObjIDList-1=30528944
        r = get('http://' + cameraIP + ':8615/MobileConnectedCamera/ObjParsingExifHeaderList?ListNum=1&ObjIDList-1=' + str(objID1))
        thumbBytes = extractThumbFromExifHeader(r.content)