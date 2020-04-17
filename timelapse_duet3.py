# Duet_3_6HC_Time_Lapse
# Copyright (C) {2020}  {JimsJump.com}
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
### What does this program do ??? ###
# Python script to collect photos & create video of 3D Printer Layer Changes
# using the Duet 3 - 6HC Mainboard (from Duet3D) and Raspberry Pi SBC
###
#
# Setup libraries
import os
import datetime
import urllib3
import subprocess
import select
import requests
import signal
from systemd import journal

urllib3.disable_warnings()

### SETUP PARAMETERS ###
#
# Requires MJPEG-Streamer & FFMPEG Installed/setup to capture pictures and compile video
# See https://github.com/cncjs/cncjs/wiki/Setup-Guide:-Raspberry-Pi-%7C-MJPEG-Streamer-Install-&-Setup-&-FFMpeg-Recording
# 
# URL & Port where webcam is at - verify by visiting in browser (Chrome/Firefox/IE etc.)
webcam_url = 'http://xxx.xxx.xxx.xxx:8081/?action=snapshot' # <-- CHANGE IP & PORT 
# polling cycle m-sec, 1000 m-sec = 1 second
cycle = 250
# define the folder access rights
access_rights = 0o777  #use 0o755 for tigher control, 0o777 grants full read/write/modify access

### setup folder locations ###
# folders are created in the same folder the script is started
# folders are have date and time stamp in names to id and locate easily
# folder where this script is stored
current_path = os.getcwd()
# create unique folder for snapshots & videos
# setup directories and notify
current_path = os.getcwd()
now = datetime.datetime.now()
timelapse_path = os.path.join(current_path, 'Video_' + now.strftime("%Y%m%dT%H%M%S") + '')
os.makedirs(timelapse_path, access_rights)
snapshots_path = os.path.join(timelapse_path, 'Images_'+ now.strftime("%Y%m%dT%H%M%S") + '')
os.makedirs(snapshots_path, access_rights)
# announce where folders are located for this run
print ("The current working directory is %s" % current_path)
print ("The time lapse video directory is %s" % timelapse_path)
print ("The snapshot images directory is %s" % snapshots_path)

# Create a systemd.journal.Reader instance 
j = journal.Reader()

# Set the reader's default log level
j.log_level(journal.LOG_INFO)

# Only include entries since the current box has booted.
j.this_boot()
j.this_machine()

# Filter log entries to Duet3 Control Server
j.add_match(_SYSTEMD_UNIT="duetcontrolserver.service")

# Move to the end of the journal
j.seek_tail()

# Important! - Discard old journal entries
j.get_previous()

# Create a poll object for journal entries
p = select.poll()
p.register(j, j.get_events())

# Register the journal's file descriptor with the polling object.
journal_fd = j.fileno()
poll_event_mask = j.get_events()
p.register(journal_fd, poll_event_mask)

# announce Time Lapse started
print('Time lapse cycles started... %s' % datetime.datetime.now())
layers = 0

# Poll for new journal entries every 250ms
# Update and take photos when the Duet Control Server announces LAYER_CHANGE, PRINT_STARTED, & PRINT_COMPLETE
# Anouncements are sent via GCODE using M118 P0 S"LAYER_CHANGE" for example
# Adding these announcements to GCODE via SLIC3R or CURA or other STL slicing program is covered in the README
while True :
    if p.poll(cycle) :
        if j.process() != journal.APPEND :
            continue
        for entry in j:
            if entry['MESSAGE'] != "" :
                # Capture Image at Layer Change
                if entry['MESSAGE'] == "[info] LAYER_CHANGE" :
                    r = requests.get(webcam_url, timeout=5, stream=True)
                    if r.status_code == 200:
                        now = datetime.datetime.now()
                        pic = os.path.join(snapshots_path, now.strftime("%Y%m%dT%H%M%S")+ "_layer_" + str(layers) + ".jpg")
                        with open(pic, 'wb') as f:
                            for chunk in r:
                                f.write(chunk)
                        print((str(entry['__REALTIME_TIMESTAMP'] )+ ' ' + entry['MESSAGE']) + ' ' + 'SNAPSHOT TAKEN AT LAYER No. ' + str(layers) )
                        layers += 1
                    else:
                        print((str(entry['__REALTIME_TIMESTAMP'] )+ ' ' + entry['MESSAGE']) + ' ' + '** SNAPSHOT FAILED!! **.')

                # Log / Announce Print Started
                if entry['MESSAGE'] == "[info] PRINT_STARTED":
                    print((str(entry['__REALTIME_TIMESTAMP'] )+ ' ' + entry['MESSAGE']) + ' ' )

                # FFMPEG Compile Video File
                if entry['MESSAGE'] == "[info] PRINT_COMPLETE":
                    # capture last layer image
                    r = requests.get(webcam_url, timeout=5, stream=True)
                    if r.status_code == 200:
                        now = datetime.datetime.now()
                        pic = os.path.join(snapshots_path, now.strftime("%Y%m%dT%H%M%S")+ "_layer_" + str(layers) + ".jpg")
                        with open(pic, 'wb') as f:
                            for chunk in r:
                                f.write(chunk)
                    # announce Print Completed
                    print((str(entry['__REALTIME_TIMESTAMP'] )+ ' ' + entry['MESSAGE']) + ' ' + 'SNAPSHOT TAKEN AT LAYER No. ' + str(layers) )
                    layers += 1
                    # compile video
                    now = datetime.datetime.now()
                    video_file = os.path.abspath(os.path.join(timelapse_path, now.strftime("%Y%m%dT%H%M%S") + ".mp4"))
                    snapshots_files = os.path.join(snapshots_path, "*.jpg")
                    print('Compiling Video... %s' % datetime.datetime.now())
                    subprocess.call(["ffmpeg", "-r", "20", "-y", "-pattern_type", "glob", "-i", snapshots_files, "-vcodec", "libx264", video_file])
                    # announce Time Lapse completed
                    print((str(entry['__REALTIME_TIMESTAMP'] )+ ' ' + entry['MESSAGE']) + ' ' )
                    # give file locations
                    print('Video located at: ' + video_file)
                    print('Snapshots located at: ' + snapshots_path)
                    # stop poll cycle
                    print('Total layers printed: ' + str(layers))
                    print('Process completed!! --Goodbye...')
                    # kill the process
                    os.kill(p.pid,signal.SIGINT)                   

   # print('waiting ... %s' % datetime.datetime.now()) #un-comment for testing to verify activity
