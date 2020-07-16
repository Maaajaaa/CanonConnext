# CanonConnext
Prototype of a FOSS Canon Connect App for Connecting to Canon Cameras via WiFi

So far you can connect to the camera (using the camera's hotspot), browse the picture and video thumbnails in the gui and download JPEG-images (no CR2 and video yet) and use the remote shoot feature when you have gphoto2 or similar.

# Run and Install

required pip3 libraries:
```pip3 install bitarray exifread requests-toolbelt```

additionally you need [my python3 port](https://github.com/SparkyCola/ptpip) of [@mmattes](https://github.com/SparkyCola/ptpip/commits?author=mmattes)' ptpip. Just copy the ptpip/ptpip.py into the CanonConnext folder.

Notes:
- you might have to change the interface name in/around line 40
- start after you're connected to the hotspot of the camera

# Tanks to
- [Stackoverflow](https://stackoverflow.com)
