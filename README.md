# Duet_3_6HC_Time_Lapse
Create time lapse videos with your Duet 3 - 6HC Mainboard, mainly meant for 3D Printers, but can be used for other machines too.

Designed to run on a Raspberry Pi and may be adaptable to other Linux platforms. Supports cameras via USB, Pi (ribbon cable), and Webcam. Produces photos and renders a video using MJPEG-Streamer & FFMPEG. Creates a sub-folders for photos and video with date and time stamps for each.

## Notes
As the printer changes layers, Duet Web Control (DWC) will post PRINT_STARTED, LAYER_CHANGE, and PRINT_COMPLETE while the printer is operating and log them in the Duet Control Server Service.  The program uses these cues to monitor the service for changes and then to have M-JPEG take photos and store them so FFMPEG can then compile the time lapse video. To see the journal posts from the Duet Web Control enter the following:
```
sudo journalctl -f -u duetcontrolserver
```
Note this idea was originally conceived by Danal in the post here: https://forum.duet3d.com/topic/14055/random-duet3-sbc-questions/8
Danal also has a more advanced Time Lapse here: https://github.com/DanalEstes/DuetLapse

## Status
Considered a well refined release at this point - not a super advanced code; but, small and does the job.

## REQUIREMENTS - Linux User level 3 out of 5
* Familarity with Linux  terminal and a Raspberry Pi using Python.
* Familarity with setting up your slicer software to make additional GCODE at layer changes.
* Verified working with Slic3r 2.2.0

### Supporting Software: PIP & Python Libraries
A stock Raspberry Pi build for the Duet 3 - 6HC Mainboard lacks needed software to support the code.  Python needs PIP and several libraries to be installed. Install the following using a terminal:

#### Ensure Linux is up to date
```
sudo apt update
sudo apt-get update
sudo apt-get upgrade
```

#### Add Python PIP 
```
sudo apt-get install python3-pip
sudo apt-get install python-pip
```

#### Python Imaging Library
```
sudo pip3 install Pillow
sudo pip install PIL 
sudo apt-get install python-imaging
```

#### Python Developer Libraries
```
sudo apt-get install python-dev
sudo apt-get install python-requests
```

#### Enable Python Systemd Libraries
```
sudo apt-get install python3-systemd
sudo apt-get install python-systemd
```

#### Enable journal-gateway:
```
sudo apt-get install systemd-devel
sudo apt-get install build-essential
sudo apt-get install libsystemd-dev
sudo apt-get install libsystemd-daemon-dev
sudo apt-get install systemd-journal-remote
sudo systemctl enable --now systemd-journal-gatewayd
```
 
### M-JPEG Streamer & FFMPEG
See https://github.com/cncjs/cncjs/wiki/Setup-Guide:-Raspberry-Pi-%7C-MJPEG-Streamer-Install-&-Setup-&-FFMpeg-Recording for more information on how to install on your Raspberry Pi.  Using a USB camera? Take the extra time to review the setup and include the "-y" option.

## Verify Camera Setup
Once everything is installed, verify the camera is setup with M-JPEG-Streamer.
In any browser Chrome/Firefox/Edge etc, access the camera's URL
URL should look similar to this:
http://127.0.0.1:8081
Live image similar to this:
http://127.0.0.1:8081/stream_simple.html
NOTE: your URL and port numbers will likely be different than these but same as what was setup in the M-JPEG Streamer & FFMPEG requirement above.

## Slicer Setup
Your slicer program (Like Slic3r or Cura or other) will need to insert GCODE at the following

### Print Started - Insert code below at top of the GCODE
```
; Time lapse - start print
M118 P0 S"PRINT_STARTED"   ; announce print has started
```

### Layer Changes - Insert code below before next layer change
```
; Time lapse - end of layer - take photo 
G1 X30 Y190 F6000        ; move head out of camera way Optional but works very good, change position depending on your camera setup
M400                     ; wait for all movement to complete
M118 P0 S"LAYER_CHANGE"  ; take a picture
G4 P1000                 ; wait a bit, P1000 = 1 second
```

### Print Completion - Insert code below at bottom of the GCODE
```
; Time lapse - complete print
G1 X30 Y190               ; move head out of camera way Optional but works very good, change position depending on your camera setup
M400                      ; wait for all movement to complete
M118 P0 S"PRINT_COMPLETE" ; take final picture
G4 P500                   ; wait a bit
```

## Usage

On the Raspberry Pi, copy the file "timelapse_duet3.py" to the folder where you want to store the time lapse photos and video. 

In a new terminal, enter the below
```
python3 timelapse_duet3.py
```
The program will now wait/scan the system journal for entries from the Duet Control Server Service.

Start your 3D print and as the printer completes the GCODE, photos will be taken and stored to a unique sub-folder with a date and time stamp.
When the print completes, the program will have FFMPEG compile the video and store in the same folder.  Once complete, the program will self terminate.

## Notes and feedback

Feel free to contact me for questions about the code; however, as each installation is unique, I won't field questions on the M-JPEG and FFMPEG installation.

Happy Time Lapses!!
