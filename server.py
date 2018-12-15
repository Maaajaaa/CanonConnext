#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Dec 13 20:02:24 2018

@author: mattis
"""
 
from http.server import HTTPServer, SimpleHTTPRequestHandler, HTTPStatus
from io import BytesIO
import os

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
            print('Status Stop request handled')
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

