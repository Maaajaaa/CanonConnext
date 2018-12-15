#/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Dec 15 05:49:57 2018

@author: mattis
"""

from http.server import HTTPServer, SimpleHTTPRequestHandler
import os
import urllib3

# HTTPRequestHandler class
class testHTTPServer_RequestHandler(SimpleHTTPRequestHandler):  
    gotAskedForCCM = False
    def do_GET(self):
        """Serve a GET request and send a request RIGHT after we get asked for CameraConnectedMobile.xml the first time to skip long waits"""
        f = self.send_head()
        if f:
            try:
                self.copyfile(f, self.wfile)
                fname = os.path.basename(f.name)
                if self.gotAskedForCCM is False and 'CameraConnectedMobile.xml' in fname:
                    self.gotAskedForCCM = True                
                    http = urllib3.PoolManager()
                    r = http.request('GET', 'http://192.168.0.106:49152/desc_iml/MobileConnectedCamera.xml?uuid=7B788B31-EC1E-445A-B5EF-243274B188F6', preload_content=False)
                    while True:
                        MobileConnectedCamera = r.read()
                        if not MobileConnectedCamera:
                            break
                        print("\n\nGot MobileConnectedCamera.xml:\n")
                        print(MobileConnectedCamera)
                        print("\n\n")
                    r.release_conn()
            finally:
                f.close()

 
def run():
  print('starting server...')
 
  # Server settings
  # Choose port 8615 for Canon imink protocol
  server_address = ('', 49152)
  httpd = HTTPServer(server_address, testHTTPServer_RequestHandler)  
  print('running server...')
  httpd.serve_forever()
 
 
run()

