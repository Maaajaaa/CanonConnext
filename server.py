#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Dec 13 20:02:24 2018

@author: mattis
"""
 
from http.server import HTTPServer, SimpleHTTPRequestHandler, HTTPStatus
from io import BytesIO
import os
from requests import Request, Session
import time

import socket
import netifaces as ni

def synScan(target='192.168.0.106', port=7):
    sock = socket.socket(ni.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(10)
    result = sock.connect_ex((target, port))
    return result
    
# HTTPRequestHandler class
class testHTTPServer_RequestHandler(SimpleHTTPRequestHandler):  
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
        """
        <ParamSet xmlns="urn:schemas-canon-com:service:CameraConnectedMobileService:1">
          <Status>Run</Status>
        </ParamSet>
        """
        if '<Status>Run</Status>' in bodyStr:
            requestKnown = True
            #TODO: put this in a try loop
            with open('GETreplies/statusRunReply.xml') as replyFile:
                    replyStr = replyFile.read()  
                    self.sendResponse(replyStr)                     
            print('Status Run request handled')
            return
            
        #Acknowledge CapabilityInfo
        """
        <ParamSet xmlns="urn:schemas-canon-com:service:CameraConnectedMobileService:1">
          <Pull_Operating>TRUE</Pull_Operating>
          <GPS_Operating>TRUE</GPS_Operating>
          <RemoteCapture_Operating>TRUE</RemoteCapture_Operating>
          <ConnectionMode>1</ConnectionMode>
          <GroupType>Basic</GroupType>
          <CustomMode>ModeA&amp;ModeC</CustomMode>
        </ParamSet>
        """
        if '<Pull_Operating>' in bodyStr:
            requestKnown = True
            with open('GETreplies/null.xml') as replyFile:
                    replyStr = replyFile.read()
                    self.sendResponse(replyStr)
            print('CapabilityInfo acknowledged')
            return
            
        #Acknowledge CameraInfo
        """
        <ParamSet xmlns="urn:schemas-canon-com:service:CameraConnectedMobileService:1">
          <CardProtect>FALSE</CardProtect>
        </ParamSet>
        """
        if '<CardProtect>' in bodyStr:
            requestKnown = True
            with open('GETreplies/null.xml') as replyFile:
                    replyStr = replyFile.read()
                    self.sendResponse(replyStr)      
            print('CameraInfo acknowledged')
            return
        
        #Acknowledge NCFData
        """
        <ParamSet xmlns="urn:schemas-canon-com:service:CameraConnectedMobileService:1">
          <AARData>jp.co.canon.ic.cameraconnect</AARData>
          <URIData>canon-a01</URIData>
        </ParamSet>
        """
        if '<AARData>' in bodyStr:
            requestKnown = True
            with open('GETreplies/null.xml') as replyFile:
                    replyStr = replyFile.read()
                    self.sendResponse(replyStr)      
            print('NFCData acknowledged')
            return
        
        #Detect Status Stop
        """
        <ParamSet xmlns="urn:schemas-canon-com:service:CameraConnectedMobileService:1">
          <Status>Stop</Status>
        </ParamSet>
        """
        if '<Status>Stop</Status>' in bodyStr:
            requestKnown = True
            #TODO: put this in a try loop
            with open('GETreplies/statusStopReply.xml') as replyFile:
                    replyStr = replyFile.read()  
                    self.sendResponse(replyStr)                     
            print('Status Stop request handled, trying to POST StatusRunRequest after some SSDP')
            with open('POSTrequests/statusRunRequest.xml') as requestFile:
                
                
                ## WAAAAAAAAAAY too messy!!!!!!!!!!!!!!
                #TODO: UNMESS
                
                #------- SEND SSDP (don't ask me why) 
                
                notifyExtension = ['' for x in range(4)]
                
                ip = ni.ifaddresses('wlp3s0')[ni.AF_INET][0]['addr']
                print(ip)
                host_port = '49152'
                
                # DEVICE SETTINGS
                
                #TODO: create unique uuid when name changes, f.e. constant+name's MD5 or so
                
                uuid = '7B788B31-EC1E-445A-B5EF-243274B188F6'
                #os and name should not contain some characters like /
                os = 'Debian 9'
                friendly_name = 'Cannon Connext'

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
                s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
                s.settimeout(3)
                for j in range(4):
                    s.sendto(str.encode(notifyBase + notifyExtension[i]), ('239.255.255.250', 1900) )
                
                #http = urllib3.PoolManager()
                #r = http.request('POST', 'http://192.168.0.106:8615/MobileConnectedCamera/UsecaseStatus?Name=ObjectPull&MajorVersion=1&MinorVersion=0', )
                s = Session()

                req = Request('POST', 'http://192.168.0.106:8615/MobileConnectedCamera/UsecaseStatus?Name=ObjectPull&MajorVersion=1&MinorVersion=0', data=str.encode(requestFile.read()))
                prepped = req.prepare()
                
                prepped.headers['Content-Type'] = 'text/xml ; charset=utf-8'
                
                #resp = s.send(prepped)
                #print(resp.status_code, resp.content)
                
                for i in range(40):
                    time.sleep(1)
                    synScan()   
                
                req = Request('POST', 'http://192.168.0.106:8615/MobileConnectedCamera/ObjIDList?StartIndex=1&MaxNum=1&ObjType=ALL')
                prepped = req.prepare()
                
                prepped.headers['Content-Type'] = 'text/xml ; charset=utf-8'
                
                #resp = s.send(prepped)
                #print(resp.status_code, resp.content)
                
            """r = requests.post('')
            print('We got something, do we?')
            print(r.status_code, r.reason)
            print(r.text)"""
                
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

 
def run():
  print('starting server...')
 
  # Server settings
  # Choose port 8615 for Canon imink protocol
  server_address = ('', 8615)
  httpd = HTTPServer(server_address, testHTTPServer_RequestHandler)  
  print('running server...')
  httpd.serve_forever()
 
 
run()

