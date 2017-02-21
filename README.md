# YAPSFrame
Yet Another (Raspberry) Pi Smart Frame

##Dependencies
Raspberry Pi Pixel using Python 2.7
```
sudo apt-get install python-imaging-tk
sudo pip install config
sudo pip install pysmb
```

Raspberry Pi Pixel using Python 3
```
sudo apt-get install python3-tk
sudo apt-get install python3-pil.imagetk
sudo pip3 install config
sudo pip3 install pysmb
```

##ToDo
* rename config_EXAMPLE.py to config.py
..** edit config.py to include your information

###Set Locale
```
sudo dpkg-reconfigure locales
```
Deselect UK (with space bar) and Select US (with spacebar)

###Set TimeZone
```
sudo dpkg-reconfigure tzdata
```

###Disable screen blanking
add following to /etc/lightdm/lightdm.conf
```
[SeatDefaults]
xserver~command=X -s 0 -dpms
```
