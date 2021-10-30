# tello3_video
steer the Tello quadrocopter with a gamepad (optional), receive video and optionally write a video file

This program was derived from the official Tello3.py demo program. 
The video stream is received and decoded using OpenCV (ffmpeg). 
You may enter commands like "takeoff", like in the official demo program. 
Because it is not much fun operating the console while the blue and red messages clog the screen (how to get rid of them?), 
I added support for a gamepad. 

This program is offered under the Creative Commons License, free of charge and without any warranty or liability. 

## features
* intuitive gamepad control 
* Soft reactions to stick inputs via an expo function 
* Decent video quality without jerks or jumps (more or less)
* Possibility to use custom codecs and video file formats 
* Documented and (hopefully) easy to read source code  

## Requirements
* You need a device (PC,...) with Python 3 installed. 
* Additional Python libraries, see first lines of source code 
* A Tello quadrocopter by Ryze Robotics, SDK 1.3 or higher. Tello EDU works well, too. 
* Optionally you can use a gamepad, connected to your device 
* Tested under Windows 10, Python 3.7.0, Tello  SDK 2.0, 8bitDO SN30 Pro+ bluetooth gamepad 

## how to use it

Power up Tello and have your PC set up to establish a WIFI connection to Tello, power up the gamepad

Open a shell (command line) window, start tello3_video, optionally adding command line parameters as described in the help menu (command line parameter -h)

The program will wait until the WIFI connection is established. If you use a gamepad, it will give a short vibration once the WIFI connection is running

When you enter "video" or press the left shoulder button of the gamepd, the video stream starts. Depending upon the -d and -w parameters, the video is displayed and/or written to file. 

Entering "oediv" ("video", read from right to left) or pressing the right shoulder button stops the video 

You can try various video codecs and file formats, using the -c and -e parameters. 

Takeoff: 
* Enter "takeoff" or press the "north" button on the gamepad
* Enter "start" or press the "start" button on the gamepad to start the motors. When Tello is parked powered up, this prevents overheating. To takeoff, move the left stick forward (going up). 

Land:
Enter "land" or press the "south" button

Emergency:
To prevent an otherwise inevitable collision, press the "select" button or the push one of the Thumb buttons. The motors will stop immediately and Tello falls down. On the keyboard, enter "emergency".  

Ending the program: Enter "end" on the shell or press the "east" button on the gamepad. Please note that the gamepad task ist still waiting for an imput when you enter "end", so move any control of the gamepad to end. Vice versa, when you end the program via gamepad, the console imput is still waiting. Press "enter" to end the program. 

Please refer to the source code to see more controls of the gamepad you can use. 

## Bugs and limitations

* Blue and red messages from ffmpeg 
* Occasional error messages, but it seems to work 
* Ending the program with keyboard and gamepad as described above 

# Have fun, I hope you enjoy flying and filming 
