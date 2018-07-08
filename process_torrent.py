#!C:\Python27\pythonw.exe
#
# process_torrent.py version 0.2
#
# Copyright (c) 2018 danielbmarshall
# Original copyright and credit goes to Filebot forums user "scudstone" 2015.
# See: https://forum.deluge-torrent.org/viewtopic.php?f=9&t=40649&start=20#p213779
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.


import subprocess
from sys import argv, exit
import os.path
import re

filename = argv[2]
filepath = argv[3]

################################################
#
# Configuration Settings
#
################################################

# If you want to send notifications to growl, you must install gntp
# Installing Python and setting Path Variable See: 
# https://www.londonappdeveloper.com/setting-up-your-windows-10-system-for-python-development-pydev-eclipse-python/
# Installing GNTP See: https://pypi.python.org/pypi/gntp
# Installing PIP See: https://pypi.org/project/pip/
# Installing Growl for Windows See: http://www.growlforwindows.com/gfw/
send_growl_notifications = True

# You should be able to leave this as-is unless your growl
# is running remote, or requires authentication
growl_hostname = "localhost"
growl_password = ""

# This is the filebot command that is executed. You can tweak the options
# as needed.  See http://www.filebot.net/forums/viewtopic.php?t=215#p1561
# for more information on available options
filebot_cmd = [
    r'C:\Users\<REPLACE WITH WINDOWS ACCOUNT NAME>\AppData\Local\Microsoft\WindowsApps\filebot.exe',

    # I recommend replacing 'fn:amc' with the path to a locally saved copy of
    # amc.groovy. 'fn:amc' downloads the script every time you run filebot.exe
    # from filebot.net.  If filebot.net is down, your file processing won't be
    # able to run. You can download the script from here:
    # https://github.com/filebot/scripts/blob/devel/amc.groovy
    '-script', 'fn:amc',
	    
    # If you end your path with a slash, then you must escape it with a second 
    # slash i.e. 'X:\\' instead of 'X:\' 
    '--output', r'X:\\',

    # Save log files to same directory where this script file is located
    '--log-file', os.path.join(os.path.dirname(os.path.realpath(__file__)), 'amc.log'),
    '--action', 'copy',
    '--conflict', 'auto',
    '-non-strict',
    '--def', 'artwork=y',
    'ut_dir={0}\{1}'.format(filepath, filename),
    'ut_kind=multi',
    'ut_title={0}'.format(filename),
    # Specify Movie and TV Series Renaming Formats and copy/move locations
    '--def', 'movieFormat=x:/Movies2/{NY}/{n.space(\'.\')} ({y})', 'seriesFormat=x:/tv2/{n}/{\'Season \'+s}/{n}.{s00e00}.{t}',
    '--def', 'subtitles=en',
    '--def', 'deleteAfterExtract=y',
    '--def', 'clean=y',

    # If you don't have Plex, remove this option
    # Obtaining your Plex Token See: https://support.plex.tv/articles/204059436-finding-an-authentication-token-x-plex-token/
    '--def', 'plex=localhost:THIS IS YOUR PLEX TOKEN'
    ]

################################################

if send_growl_notifications:
    import gntp.notifier

    
class GrowlHelper():
    def __init__(self):
        try:
            icon = open(os.path.join(os.path.dirname(
                os.path.realpath(__file__)), 'filebot.logo.png'), 'rb').read()
        except IOError:
            icon = None

        self._growl = gntp.notifier.GrowlNotifier(
            applicationName = "Filebot",
            applicationIcon = icon,
            notifications = ["Rename Successful","Rename Failed"],
            defaultNotifications = ["Rename Successful", "Rename Failed"],
            hostname = growl_hostname,
            password = growl_password
            )

        self._growl.register()

    def success_notify(self, description):
        self._growl.notify(
            noteType = "Rename Successful",
            title = "Rename Successful",
            description = description,
            sticky = False,
            priority = 1,
        )

    def failure_notify(self, description):
        self._growl.notify(
            noteType = "Rename Failed",
            title = "Rename Failed",
            description = description,
            sticky = False,
            priority = 1,
        )


def cleanup_success(filename, msg):
    output = [filename, "\n"]

    for line in msg.splitlines():
        if re.match("^\[COPY\] Rename \[.+\] to \[.+\]$", line):
            output.append(line)

    return "\n".join(output)

    
def cleanup_failure(filename, msg):
    output = [filename, "\n"]
    for line in msg.splitlines():
        if re.match("Java HotSpot.+", line):
            continue

        output.append(line)

    return "\n".join(output)

    
def main():
    # Set subprocess flags to allow filebot to be called without
    # popping up a console screen
    startupinfo = subprocess.STARTUPINFO()
    startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    pid = subprocess.Popen(filebot_cmd,
                           stdout=subprocess.PIPE,
                           stderr=subprocess.PIPE,
                           startupinfo=startupinfo)
    stdout, stderr = pid.communicate()

    if send_growl_notifications:
        growl = GrowlHelper()
        if pid.returncode != 0:
            growl.failure_notify(cleanup_failure(filename, stderr))
        else:
            growl.success_notify(cleanup_success(filename, stdout))


    return pid.returncode

    
if __name__ == "__main__":
    exit(main())
