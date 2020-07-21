#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Dec  4 17:10:05 2018

"""

import socket
import netifaces as ni
from io import BytesIO, BufferedRandom
from requests import Request, Session, get
from time import sleep
import re
import xml.etree.cElementTree as ET
from http.server import HTTPServer, SimpleHTTPRequestHandler, HTTPStatus
import os
import threading
from bitarray import bitarray
import exifread
import sys
from PyQt5 import QtWidgets
from PyQt5.QtGui import QIcon, QPixmap, QTransform
from PyQt5.QtWidgets import QMainWindow, QListWidget, QListWidgetItem, \
    QAbstractItemView, QAction, QProgressDialog
from PyQt5.QtCore import QSize, QThread, QObject, pyqtSignal, Qt
from requests_toolbelt.multipart import decoder
# import qdarkstyle\
from ptpip_mattis import PtpIpConnection
from ptpip_mattis import PtpIpCmdRequest
from threading import Thread


# ---- GLOBAL VARIABLES -------

runSSDPOnAndOn = True
connectedToCamera = False
debug = True

cameraIP = ''
cameraObjects = []
totalNumOfItemsOnCamera = 0

# GLOBAL TODO: put try-catch into every request
for iface in ni.interfaces():
    # temporary fix for the problem of having multiple interfaces and choosing the right one
    if iface == 'wlp3s0':
    # if iface == 'enp2s0':
        if ni.AF_INET in ni.ifaddresses(iface):
            possibleIp = ni.ifaddresses(iface)[ni.AF_INET][0]['addr']
            if possibleIp != '127.0.0.1':
                global ip
                ip = possibleIp
                break
print(ip)
if not ip:
    print("ERROR: could not get device's IP-Adress")
    sys.exit(1)

host_port = '49152'

# DEVICE SETTINGS

# TODO: create unique uuid when name changes, f.e. constant+name's MD5 or so
uuid = '7B788B31-EC1E-445A-B5EF-243274B188F6'

# os and name should not contain /
system = 'Debian 9'
friendly_name = 'Cannon Connext'

# ------------SSDP NOTIFY Messages--------------------
notifyBase = ''
notifyExtension = ['' for x in range(4)]


gotData = 0
data = ''

# constants to make life easy

ffd8 = bitarray()
ffd8.frombytes(b'\xFF\xD8')
ffd9 = bitarray()
ffd9.frombytes(b'\xFF\xD9')


# HTTPRequestHandler class
class iminkRequestHandler(SimpleHTTPRequestHandler):
    CCMRequested = False
    server_version = 'OS/Version UPnP/1.0'
    sys_version = 'UPeNd/1.5 cHttpdHandlerSock'

    def do_POST(self):
        """Methode to handle POST requests."""
        content_length = int(self.headers['Content-Length'])
        body = self.rfile.read(content_length)
        bodyStr = body.decode('utf-8')
        requestKnown = False

        # Detecting Run status request and answering with statusReplyRun.xml:
        if '<Status>Run</Status>' in bodyStr:
            requestKnown = True
            # TODO: put this in a try loop
            with open('GETreplies/statusRunReply.xml') as replyFile:
                    replyStr = replyFile.read()
                    self.sendResponse(replyStr)
            if debug:print('Status Run request handled')
            return

        # Acknowledge CapabilityInfo
        if '<Pull_Operating>' in bodyStr:
            requestKnown = True
            with open('GETreplies/null.xml') as replyFile:
                    replyStr = replyFile.read()
                    self.sendResponse(replyStr)
            if debug:print('CapabilityInfo acknowledged')
            return

        # Acknowledge CameraInfo
        if '<CardProtect>' in bodyStr:
            requestKnown = True
            with open('GETreplies/null.xml') as replyFile:
                    replyStr = replyFile.read()
                    self.sendResponse(replyStr)
            if debug:print('CameraInfo acknowledged')
            return

        # Acknowledge NCFData
        if '<AARData>' in bodyStr:
            requestKnown = True
            with open('GETreplies/null.xml') as replyFile:
                    replyStr = replyFile.read()
                    self.sendResponse(replyStr)
            if debug:print('NFCData acknowledged')
            return

        # Detect Status Stop
        if '<Status>Stop</Status>' in bodyStr:
            requestKnown = True
            # TODO: put this in a try loop
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
        # header
        content_length = len(str.encode(bodyStr))
        if content_length == 0:
            self.send_response_only(HTTPStatus.OK)
            self.send_header("Content-Length", content_length)
            self.send_header('Server', self.version_string())
            self.send_header('Date', self.date_time_string())
        else:
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Length", content_length)
        if content_length != 0:
            self.send_header("Content-Type", 'text/xml ; charset=utf-8')
        self.end_headers()
        response = BytesIO()
        response.write(str.encode(bodyStr))
        self.wfile.write(response.getvalue())

    def do_GET(self):
        """Serve a GET request and send a request RIGHT after CameraConnectedMobile.xml is requestested for the first time"""
        f = self.send_head()
        if f:
            try:
                self.copyfile(f, self.wfile)
                fname = os.path.basename(f.name)
                if self.CCMRequested is False and 'CameraConnectedMobile.xml' in fname:
                    self.CCMRequested = True
            finally:
                f.close()

def imink_response_sever():
    print('starting server in separate thread')
    # change dir to serverFiles
    server_address = ('', 8615)
    server = HTTPServer(server_address, iminkRequestHandler)
    server.serve_forever()


class SSDP_RequestHandler(SimpleHTTPRequestHandler):
    # CameraConnectedMobile Request tracking variable, if camera requests it, SSDP-Server can be stopped
    CCMRequested = False
    def do_GET(self):
        """Serve a GET request and send a GET request RIGHT after request for
           CameraConnectedMobile.xml the first time to skip long waits"""
        f = self.send_head()
        global cameraIP
        cameraIP, port = self.client_address
        if f:
            try:
                self.copyfile(f, self.wfile)
                fname = os.path.basename(f.name)
                if self.CCMRequested is False and 'CameraConnectedMobile.xml' in fname:
                    self.CCMRequested = True
                    global runSSDPOnAndOn
                    runSSDPOnAndOn = False

                    r = get('http://' + cameraIP + ':49152/desc_iml/MobileConnectedCamera.xml?uuid=7B788B31-EC1E-445A-B5EF-243274B188F6')
                    MobileConnectedCamera = r.text
                    if debug: print("\n\nGot MobileConnectedCamera.xml:\n", MobileConnectedCamera, "\n\n")
            finally:
                f.close()


def start_ssdp_response_server():
    print('starting server in separate thread')
    # change dir to serverFiles
    server_address = ('', 49152)
    server = HTTPServer(server_address, SSDP_RequestHandler)
    server.serve_forever()


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

def defineNotifications(stage):
    """set notifyBase and notifyExtension to the right stage"""

    global notifyBase, notifyExtension

    if stage == 'alive':
        # proper introduction
        notifyBase =  \
            'NOTIFY * HTTP/1.1\r\n' \
            'Host: 239.255.255.250:1900\r\n' \
            'Cache-Control: max-age=1800\r\n' \
            'Location: http://'+ ip + ':' + host_port + '/MobileDevDesc.xml\r\n' \
            'Server: Camera OS/1.0 UPnP/1.0 ' + system + '/' + friendly_name + '/1.0\r\n'\
            'NTS: ssdp:alive\r\n' \

        notifyExtension[0] = \
            'NT: upnp:rootdevice\r\n' \
            'USN: uuid:' + uuid + '::upnp:rootdevice\r\n' \
            '\r\n'

        notifyExtension[1] = \
            'NT: uuid:' + uuid + '\r\n' \
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

    if stage == 'byebye':
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

    # listen for 3 seconds
    # this is a bad way but should do it for now, will cause issues when other Upnp devices are in the same network
    try:
        while True:
            data, addr = s.recvfrom(65507)
            if data!="":
                gotData=1
            if debug: print(addr, data)
    except socket.timeout:
        pass


def getCameraDevDesc():
    # request and read the CameraDevDesc.xml

    global gotData, data
    if gotData:
        url = re.search("(?P<url>https?://[^\s]+)", data.decode("utf-8")).group("url")
        r = get(url)
        CameraDevDesc = r.text
        if debug: print("\n\nGot CameraDevDesc.xml:\n", CameraDevDesc, "\n\n")

def makeMobileDevDesc():
    # make MobileDevDesc.xml, modifying get's messy because of the partial namespace
    root = ET.Element('root', xmlns="urn:schemas-upnp-org:device-1-0")
    specVersion = ET.SubElement(root, 'specVersion')
    ET.SubElement(specVersion, 'major').text = '1'
    ET.SubElement(specVersion, 'minor').text = '0'
    # IP-address and port for ongoing conversation (this would be another way of hacking the system, but the camera accepts requests from
    # any device in the network once it is "connected" to a device anyway)
    ET.SubElement(root, 'URLBase').text = 'http://' + ip + ':' + host_port + '/'
    device = ET.SubElement(root, 'device')
    ET.SubElement(device, 'deviceType').text = 'urn:schemas-upnp-org:device:Basic:1'
    ET.SubElement(device, 'friendlyName').text = friendly_name
    # I know this sounds wrong, but that's what the Canon App does as well, so whatever
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
    # meaning of X_VendorExtVer unkown to me
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
    only works well in THIS case because they're all the same, the standard is
    much broader
    """

    exifbits = bitarray()
    exifbits.frombytes(exitfbytes)

    ffd8db = bitarray()
    # FFDB was found as a common thing in all thumbs
    ffd8db.frombytes(b'\xFF\xD8\xFF\xDB')

    ffd8s = exifbits.search(ffd8db)
    ffd9s = exifbits.search(ffd9)

    # cut from the occurence of ffd8ffe1 to ffd9 but incl. ffd9 (16 BITS long)
    for i in range(0, len(ffd8s)):
        if ffd9s[len(ffd9s)-1]+16 - ffd8s[i] > 0:
            exifbits = exifbits[ffd8s[i]:ffd9s[len(ffd9s)-1]+16]

            if debug:
                with open('pyExtractedThumb.jpg', 'wb') as file:
                    exifbits.tofile(file)

            return exifbits.tobytes()

def getThumb(number):
    # make sure we don't request an invalid EXIF header / thumb
    if number < totalNumOfItemsOnCamera:
        # fetch EXIF-header which contains a small thumb, remember the thumb is designed to show up on small medium-dense camera screen not a 4k tablet
        # 10.42.0.179:8615/MobileConnectedCamera/ObjParsingExifHeaderList?ListNum=1&ObjIDList-1=30528944
        r2 = get(baseURL + 'ObjParsingExifHeaderList?ListNum=1&ObjIDList-1=' + str(cameraObjects[number]['objID']))
        # TODO: do this in a new thread for a SLIGHT performance improvement if 0.02s per preview image on a shitty CPU
        #-----------------------process EXIF tags-------------------------------------------------------

        # get tags, princess exifread won't notice vincent is just three (thousand) bytes stacked in a trenchcoat
        bitcent = bitarray()
        bitcent.frombytes(r2.content)
        if cameraObjects[number]['objType'] != "CR2":
            # all other files seem to have a JPEG/exif header, even Videos
            exifstart = bitcent.search(ffd8)[0]
            vincentAdultman = BufferedRandom(BytesIO())
            vincentAdultman.write(bitcent[exifstart:len(bitcent)-exifstart].tobytes())
            vincentAdultman.seek(0)

            if debug:
                with open('r2.txt', 'wb') as txt:
                    txt.write(r2.text.encode())
            # read EXIF-tags but don't process the thumb (method below is much faster)
            tags = exifread.process_file(vincentAdultman, details=False)
            # print(tags)
            # put relevant tags into cameraObjects
            cameraObjects[number]['Resolution'] = str(tags['EXIF ExifImageWidth']) + 'x' + str(tags['EXIF ExifImageLength'])
            if int(str(tags['EXIF ExifImageWidth'])) != 160:
                cameraObjects[number]['SizeAbrv'] = getImageSizeAbbrevation(str(tags['Image Model']), str(tags['EXIF ExifImageWidth']))
            else:
                cameraObjects[number]['SizeAbrv'] = '?'
            cameraObjects[number]['Orientation'] = str(tags['Image Orientation'])
            dt = str(tags['EXIF DateTimeDigitized'])
            cameraObjects[number]['Date'] = dt.translate({ord(c): None for c in ': '})
        else:
            # it's a RAW file, the header is very different from the JPEG so it's just set to some defaults
            cameraObjects[number]['Resolution'] = 'RAW'
            # RAWs (CR2 are a subclass of them) are always unscaled
            cameraObjects[number]['SizeAbrv'] = 'L'
            # we don't know but it's not worth the effort
            cameraObjects[number]['Orientation'] = 'Horizontal'
        # save some important tags
        return extractThumbFromExifHeader(r2.content)

def getImageSizeAbbrevation(imageModel, imageWidth):
    CameraModelImageSizeAbbrevations = {
    'Canon PowerShot G7 X':{'5472':'L', '4320':'M1', '2304':'M2', '1920':'M2', '720':'S'}
    }
    return CameraModelImageSizeAbbrevations[imageModel][imageWidth]

def postFileGetResponse(url, path):
    with open(path) as requestFile:
        req = Request('POST', url, data=str.encode(requestFile.read()), headers= {'Content-Type':'text/xml ; charset=utf-8'})
    return Session().send(req.prepare())

# start server treads

GUIdevOnly = False
if not GUIdevOnly:
    ssdpThread = threading.Thread(target=start_ssdp_response_server)
    ssdpThread.start()

    iminkThread = threading.Thread(target=imink_response_sever)
    iminkThread.start()
    while not connectedToCamera:
        if runSSDPOnAndOn:
            getCameraDevDesc()
            makeMobileDevDesc()
            sendNotify(stage='alive')
            gotData=False
        else:
            sleep(0.01)

if not GUIdevOnly:

    # We're in like Flinn
    baseURL = 'http://' + cameraIP + ':8615/MobileConnectedCamera/'
    resp = postFileGetResponse(baseURL + 'UsecaseStatus?Name=ObjectPull&MajorVersion=1&MinorVersion=0', 'POSTrequests/statusRun.xml')
    if debug: print(resp.status_code, resp.content)

    resp = get(baseURL + 'ObjIDList?StartIndex=1&MaxNum=1&ObjType=ALL')

    if debug: print(resp.status_code, resp.content)
if GUIdevOnly or resp.status_code == 200:
    if not GUIdevOnly:
        # removing the namespaces makes parsing much simpler
        resultSet = ET.fromstring(removeXMLNamespace(resp.content.decode("utf-8")))
        totalNumOfItemsOnCamera = int(resultSet.find('TotalNum').text)

        """
        cameraObjects is a list, starting at the oldest object, of dictionaries
        containing objID: unique identifier of each picture given to it by the
        camera, required for loading the EXIF header and downloadig the image
        objType: type of picture/video, can be JPEG, CR2, JPEG+CR2 or MP4?
        groupNbr: number of pictures in a group of pictures taken in
        CreativeShot mode, all of them seem to be refferenced by the same ID
        """
        cameraObjects = [{} for i in range(totalNumOfItemsOnCamera)]

        # get IDs, types and groups
        objectsIndexed = 0
        while objectsIndexed < totalNumOfItemsOnCamera:
            # http://192.168.0.106:8615/MobileConnectedCamera/GroupedObjIDList?StartIndex=1&ObjType=ALL&GroupType=1
            r = get(baseURL + 'GroupedObjIDList?StartIndex=' + str(objectsIndexed +1) + '&MaxNum=100&ObjType=ALL&GroupType=1')
            resultSet = ET.fromstring(removeXMLNamespace(r.text) )
            if debug: print(resultSet)
            for listID in range(1,int(resultSet.find('ListCount').text) + 1):
                listIDStr = str(listID)
                # find dictionary entries
                groupNbr = resultSet.find('GroupedNumList-' + listIDStr).text
                objType = resultSet.find('ObjTypeList-' + listIDStr).text
                objID = resultSet.find('ObjIDList-' + listIDStr).text
                # add dictionary of current object to the listd
                cameraObjects[objectsIndexed]={'objID':objID, 'objType':objType, 'groupNbr':groupNbr}

                objectsIndexed += 1
                # picture groups from creative shots count as one item since they have only one ID afaik
                if int(groupNbr) != 0:
                    totalNumOfItemsOnCamera -= (int(groupNbr) - 1)

            if debug: print('Got soo many Elements:' + str(objectsIndexed))
        if debug: print(cameraObjects)

    # start GUI to display thumbs

    class LiveShootWindow(QMainWindow):
        def __init__(self, parent=None):
            super(LiveShootWindow, self).__init__(parent)

        def startStream(self):

            # open up a PTP/IP connection, default IP and Port is host='192.168.1.1', port=15740
            ptpip = PtpIpConnection()
            ptpip.open(host=cameraIP)

            # Start the Thread which is constantly checking the status of the camera and which is
            # processing new command packages which should be send
            thread = Thread(target=ptpip.communication_thread)
            thread.daemon = True
            thread.start()

            sleep(1.5)
            print('PTP-IP started')
            # op-code 0x9114: TP_OC_CANON_EOS_SetRemoteMode
            ptpip_cmd =  PtpIpCmdRequest(cmd=0x9114, param1=0x11)
            ptpip_packet = ptpip.cmd_queue.append(ptpip_cmd)
            print('9114 apended')
            sleep(1.5)
            # op-code 0x9115: PTP_OC_CANON_EOS_SetEventMode
            ptpip_cmd = PtpIpCmdRequest(cmd=0x9115, param1=0x2)
            ptpip_packet = ptpip.cmd_queue.append(ptpip_cmd)
            print('9115 appended')

            sleep(1.5)
            # op-code 0x9116: PTP_OC_CANON_EOS_GetEvent
            # This retrieves configuration status/updates/changes on EOS cameras. It reads a datablock which has a list of variable sized structures.
            ptpip_cmd = PtpIpCmdRequest(cmd=0x09116)
            ptpip_packet = ptpip.cmd_queue.append(ptpip_cmd)
            print('9116 appended')

            sleep(1.5)
            # op-code 0x9110: PTP_OC_CANON_EOS_SetDevicePropValueEx
            # some value(s) is/are set, in my dump it's
            '''ptpip_cmd = PtpIpCmdRequest(cmd=0x09110)
            ptpip_packet = ptpip.cmd_queue.append(ptpip_cmd)
            print('9110 sent')

            sleep(2)'''


    class HelloWindow(QMainWindow):
        def __init__(self):
            QMainWindow.__init__(self)
            # TODO: proper window sizing
            # self.setMinimumSize(QSize(1800, 1000))
            self.setWindowTitle("Cannon Connext")

            self.liveShootWindow = LiveShootWindow(self)

            self.listWidget = GalleryWidget()
            self.setCentralWidget(self.listWidget)

            exitAct = QAction(QIcon.fromTheme('application-exit'), 'Exit', self)
            exitAct.setShortcut('Ctrl+Q')
            exitAct.setStatusTip('Quit')
            exitAct.triggered.connect(self.disconnectAndClose)

            dowloadAct = QAction(QIcon.fromTheme('emblem-downloads'), 'Download selected images', self)
            dowloadAct.setShortcut('Ctrl+D')
            dowloadAct.setStatusTip('Download selected images')
            dowloadAct.triggered.connect(self.downloadSelected)

            liveviewAct = QAction(QIcon.fromTheme('camera-photo'), 'Live shoot', self)
            liveviewAct.setShortcut('Control+K')
            liveviewAct.setStatusTip('Remote live view shooting')
            liveviewAct.triggered.connect(self.startLiveview)

            self.statusBar()

            toolbar = self.addToolBar('Exit')
            toolbar.addAction(exitAct)
            toolbar.addAction(dowloadAct)
            toolbar.addAction(liveviewAct)

            self.obj= SomeObject()
            self.objThread = QThread()

        def addPic(self,pixmap,name, number):
            gi = GalleryItem(QIcon(pixmap),name)
            gi.setObjectNumber(number)
            self.listWidget.addItem(gi)

        def startLiveview(self):
            '''initiate the live view remote show window'''
            self.stopThumbLoading()
            # stop object transer
            resp = postFileGetResponse(baseURL + 'UsecaseStatus?Name=ObjectPull&MajorVersion=1&MinorVersion=0', 'POSTrequests/statusStop.xml')
            if resp.status_code == 200:
                # request the initiation of PTP
                resp = postFileGetResponse(baseURL + 'UsecaseStatus?Name=RemoteCapture&MajorVersion=1&MinorVersion=0', 'POSTrequests/statusRun.xml')
                print(resp)
                if resp.status_code == 200:
                    print("Start gphoto now, camera IP is:", cameraIP)
                    self.liveShootWindow.show()
                    self.liveShootWindow.startStream()

        def downloadSelected(self):
            '''Downlaod all selected items, further refered to as stack'''
            # stop loading thumbs
            # TODO: continue loading after download is finished
            self.stopThumbLoading()

            # show progress dialog
            progressDialog = QProgressDialog("Initiating Download ...", "Cancel", 0, 100, self)
            progressDialog.setWindowModality(Qt.WindowModal)
            progressDialog.setWindowTitle("Downloading " + str(len(self.listWidget.selectedItems())) + " Pictures and Videos")
            progressDialog.setMinimumDuration(0)

            # total size of stack in bits (for showing the progress indicator)
            totalSize = 0
            totalDownloadedBits = 0
            # calculate totalSize and save each item's size in order to download it
            for item in self.listWidget.selectedItems():
                currentNumber = item.getObjectNumber()
                currentID = cameraObjects[currentNumber]['objID']
                currentType = cameraObjects[currentNumber]['objType']
                # get object properties (the resolution is already parsed from EXIF but oddly the size is required to get the image)
                # http://10.42.0.179:8615/MobileConnectedCamera/ObjProperty?ObjID=30528640&ObjType=JPG
                r = get(baseURL + 'ObjProperty?ObjID=' + currentID + '&ObjType=' + currentType)
                # TODO: do better error handling here
                if r.status_code == 200:
                    # save dataSize for actual downloading
                    cameraObjects[currentNumber]['dataSize'] = int(ET.fromstring(removeXMLNamespace(r.text)).find('DataSize').text)
                    totalSize += cameraObjects[currentNumber]['dataSize']
                else:
                    print('ERROR requesting object with ID:', currentID, 'failed')
                    print("response:", r)

            # reset dialog
            progressDialog.setValue(0)
            progressDialog.setAutoClose(True)
            # Download stack
            for item in self.listWidget.selectedItems():
                currentNumber = item.getObjectNumber()
                currentID = cameraObjects[currentNumber]['objID']
                currentDataSize= cameraObjects[currentNumber]['dataSize']
                currentType = cameraObjects[currentNumber]['objType']
                receivedBytes = b''
                # the response delivers the preparation status via <ObjStatus>PREPARING</ObjStatus> (other texts haven't been observed by me)
                # and progress via <Progress>x</Progress> in the resultSet xml with x = 0-100
                url = baseURL + 'ObjData?ObjID=' + cameraObjects[currentNumber]['objID'] + '&ObjType=' + currentType + '&ResizeDataSize=' + str(currentDataSize)
                r = get(url)

                '''# get continous status updates, in the pcap they were under 0.01s apart sometimes so no need to worry about spam
                    r = get(url)
                    if r.status_code != 200:
                        print('ERROR requesting object with ID:', currentID, 'failed')
                        print("response:", r)

                    else:
                        # preparation should be done now
                        if debug: print("mp4 processing done")
                        preparingVideo = False
                        # get actal data size (converting changes it, so we might get odd looking requests, where we seem to request beyond the end because we won't change the ResizeDataSize in the requests, but don't worry Canon does the same)

                        for part in multipart_data.parts:
                            if b'application/octet-stream' in part.headers[b'Content-Type']:
                                 receivedBytes += part.content
                                 totalDownloadedBits += len(part.content)
                                 progressDialog.setValue(totalDownloadedBits)'''
                progress = -1
                while len(receivedBytes) < currentDataSize:
                    # get the image, unresized:
                    # same for MP4, except ObjType=MP4
                    # 10.42.0.179:8615/MobileConnectedCamera/ObjData?ObjID=30791920&ObjType=JPG&ResizeDataSize=679726
                    url = baseURL + 'ObjData?ObjID=' + cameraObjects[currentNumber]['objID'] + '&ObjType=' + currentType + '&ResizeDataSize=' + str(currentDataSize)
                    if len(receivedBytes) != 0:
                        url += '&Offset=' + str(len(receivedBytes))
                    r = get(url)
                    if r.status_code == 200:
                        if r.text.find('<ObjStatus>') != -1 and currentType == 'MP4':
                            #need to wait for the video to be converted on Camera, it's down to 720p30 for Canon G7X
                            if progress == -1:  progress = 0
                            progressDialog.setTextLabel("Camera is preparing video")
                            progressDialog.setMaximum(100)
                        else:
                            # set/update the progress bar
                            progress = 100
                            progressDialog.setMaximum(totalSize)
                            progressDialog.setLabelText("Downloading and saving files (" + str(round(totalSize/1000000,1)) + "MB)")

                        multipart_data = decoder.MultipartDecoder.from_response(r)
                        for part in multipart_data.parts:
                            if b'application/octet-stream' in part.headers[b'Content-Type'] and progress < 100:
                                 receivedBytes += part.content
                                 totalDownloadedBits += len(part.content)
                                 progressDialog.setValue(totalDownloadedBits)
                                 if len(receivedBytes) == currentDataSize:
                                     with open('CanonConnext/' + cameraObjects[int(currentNumber)]['Date'] + '.' + currentType, 'wb') as file:
                                        file.write(receivedBytes)
                            if progress in range(0,100) and b'text/xml' in part.headers[b'Content-Type']:
                                responseXML = part.content.decode('utf-8')
                                progressTag = ET.fromstring(removeXMLNamespace(responseXML)).find('Progress')
                                if progressTag != None:
                                    progress = int(progressTag.text)
                                    progressDialog.setValue(progress)
                                    if debug: print("Progress: ", progress)
                                #check for TotalSize which contains the size of the re-encoded video
                                sizeTag = ET.fromstring(removeXMLNamespace(responseXML)).find('TotalSize')
                                if sizeTag != None:
                                    actualDataSize = int(sizeTag.text)
                                    if debug: print("actual video size:", actualDataSize)
                                    # correct the total size
                                    totalSize = totalSize - currentDataSize + actualDataSize
                                    # empty the first set of data
                                    currentDataSize = actualDataSize
                                    # set progress to 101 to indicate that this should not be repeated
                                    progress = 101

                    else:
                        print('ERROR requesting object with ID:', currentID, 'failed')
                        print("response:", r)

        def disconnectAndClose(self):
            # tell Camera to turn off and close app
            self.stopThumbLoading()
            postFileGetResponse(baseURL + 'UsecaseStatus?Name=ObjectPull&MajorVersion=1&MinorVersion=0', 'POSTrequests/statusStop.xml')
            self.obj.shutDownCamera()
            # self.close()

        def stopThumbLoading(self):
            self.obj.stop()
            self.objThread.quit()
            self.objThread.wait()

    class GalleryWidget(QListWidget):
        def __init__(self, parent=None):
            super(GalleryWidget, self).__init__(parent)
            self.setViewMode(QListWidget.IconMode)
            self.setIconSize(QSize(200,200))
            self.setResizeMode(QListWidget.Adjust)
            self.setDragEnabled(False)
            self.setSelectionMode(QAbstractItemView.ExtendedSelection)

    class GalleryItem(QListWidgetItem):
        def setObjectNumber(self, number):
            self.objectNumber = number

        def getObjectNumber(self):
            return self.objectNumber

    class SomeObject(QObject):

        finished = pyqtSignal()
        addPic = pyqtSignal(QPixmap, str, int)
        stopNow = False

        def runner(self):
            for i in range(1,totalNumOfItemsOnCamera):
                qp = QPixmap()
                # we want to see newest first but numbering starts at oldest
                currentID = totalNumOfItemsOnCamera-i
                qp.loadFromData(getThumb(currentID))

                # rotate pixmap
                if cameraObjects[currentID]['Orientation'] ==  'Rotated 90 CW':
                    qp = qp.transformed(QTransform().rotate(90))

                if cameraObjects[currentID]['Orientation'] ==  'Rotated 90 CCW':
                    qp = qp.transformed(QTransform().rotate(270))

                self.addPic.emit(qp, cameraObjects[currentID]['objType'] + " " + cameraObjects[currentID]['SizeAbrv'], currentID)
                if self.stopNow:
                    break
            # self.finished.emit()

        def stop(self):
            self.stopNow = True

        def shutDownCamera(self):
            sleep(2)
            postFileGetResponse(baseURL + 'UsecaseStatus?Name=Disconnect&MajorVersion=1&MinorVersion=0', 'POSTrequests/statusRun.xml')
            postFileGetResponse(baseURL + 'DisconnectStatus', 'POSTrequests/powerOff.xml')
            # SSDP byebye
            sendNotify(stage='byebye')
            # ssdpThread.quit()
            # iminkThread.quit()
            self.finished.emit()

    app = QtWidgets.QApplication(sys.argv)
    # app.setStyleSheet(qdarkstyle.load_stylesheet_pyqt5())
    mainWin = HelloWindow()
    mainWin.show()
    if not GUIdevOnly:
        objThread = mainWin.objThread
        obj = mainWin.obj
        obj.moveToThread(objThread)
        obj.finished.connect(objThread.quit)
        objThread.started.connect(obj.runner)
        obj.addPic.connect(mainWin.addPic)
        obj.finished.connect(mainWin.close)
        objThread.start()
    sys.exit(app.exec_())
