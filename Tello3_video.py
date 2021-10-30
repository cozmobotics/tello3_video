# tello demo by Ryze Robotics, modified by Martin Piehslinger
# added video and gamepad support 
# learned from (among others):
# https://learnopencv.com/read-write-and-display-a-video-using-opencv-cpp-python/
# https://docs.opencv.org/4.5.1/d7/d9e/tutorial_video_write.html

import threading 
import socket
import sys
import time
import os
import inputs # for gamepad
from pythonping import ping
import argparse
import cv2

#------------------------------------------------------------------------
def waitForConnection (IpAddress):
	''' send pings to IpAddress until ping is successful. No timeout, will wait forever. '''
	Count = 0
	Connected = False
	while (not Connected):
		Count = Count + 1
		PingError = False
		try:
			PingResult = (ping(IpAddress,timeout=1,count=1))
		except Exception as e:
			print (str(e))
			PingError = True
			
		if (not PingError):
			if ((PingResult.success())):
				Connected = True
			
		if (not Connected):
			# print ('waiting for connection ' + str (Count) + ' ...')				# Python2 version
			print ('waiting for connection ' + str (Count) + ' ...', end = "\r")	# Python3 version
			time.sleep (1)

	print ("connected.")



#-----------------------------------------------------------------------------------
def recv():
	'''task to receive information from Tello. Simply print message to screen'''
	global TimeSent
	global Running
	global DataDecoded
	
	print ("Tello recv task started")
	count = 0
	while Running: 
		RecvError = False
		try:
			data, server = sock.recvfrom(1518)
		except Exception as e:
			RecvError = True
			if (str(e) == 'timed out'):
				print (".", end = "") # python2 users, please remove this line
				pass
			else:
				print ('\n------------------- Exception: ' + str(e) + '\n')
				break
		if (not RecvError):
			DataDecoded = data.decode(encoding="utf-8")
			print(DataDecoded)


#--------------------------------------------------------------
def expFunc (x):
	# ignore = 3500
	ignore = 500
	if abs(x) < ignore:
		y = 0
	else:
		if (x > 0):
			sign = 1
		else:
			sign = -1
		# sign = int(x / abs(x))
		y = sign * 100 * ((abs (x) - ignore) / (32767 - ignore)) ** 2
		y = int (y)
		
		if (y > 100):
			y = 100
		if (y < -100):
			y = -100
		
	return y
#--------------------------------------------------------------
# def expFunc (x):
	# y = int(x / 327) 
	# return y
#--------------------------------------------------------------
def rcCommand (RcArray):
	'''create a command like rc 100 100 100 100 from an array of 4 integers'''
	RcCommand = 'rc'
	for Count in range (0,4):
		stickVal = expFunc (RcArray[Count])
		RcCommand = RcCommand + ' ' + str(stickVal)
	
	# print (RcCommand)
	return (RcCommand)


#-----------------------------------------------------------------------------------
def pad():
	global Running
	global RunningVideo
	global Rc
	global sock
	
	pads = inputs.devices.gamepads
	if (len(pads) > 0):
		print ("found gamepad" + str(pads[0]))
		
		pads[0].set_vibration(1, 1, 200)
		
		while (Running):
			msgPad = ''
			events = inputs.get_gamepad()
			for event in events:
				# print(event.ev_type, event.code, event.state)
				msgPad = "" # preset
				if (event.ev_type == "Absolute"): 
					if (event.code == "ABS_X"):
						Rc[3] = event.state
						msgPad = rcCommand (Rc)
					elif (event.code == "ABS_Y"):
						Rc[2] = event.state
						msgPad = rcCommand (Rc)
					elif (event.code == "ABS_RX"):
						Rc[0] = event.state
						msgPad = rcCommand (Rc)
					elif (event.code == "ABS_RY"):
						Rc[1] = event.state
						msgPad = rcCommand (Rc)
						
					elif (event.code == "ABS_Z"):	# left trigger ... very slow rotation left
						Rc[3] = event.state * (-100)
						msgPad = rcCommand (Rc)
					elif (event.code == "ABS_RZ"):	# right trigger ... very slow rotation right
						Rc[3] = event.state * 100
						msgPad = rcCommand (Rc)
					

					elif (event.code == "ABS_HAT0X"):
						if (event.state == -1):
							msgPad = "flip l"
						elif (event.state == 1):
							msgPad = "flip r"
					elif (event.code == "ABS_HAT0Y"):
						if (event.state == -1):
							msgPad = "flip f"
						elif (event.state == 1):
							msgPad = "flip b"
					
					
				elif (str(event.ev_type) == "Key"): 
					if (event.code == "BTN_NORTH"):
						if (str(event.state) == "1"):
							msgPad = "takeoff"
					elif (event.code == "BTN_SOUTH"):
						if (str(event.state) == "1"):
							msgPad = "land"
					elif (event.code == "BTN_WEST"):
						if (str(event.state) == "1"):
							msgPad = "battery?"

					elif (event.code == "BTN_EAST"):
						if (str(event.state) == "1"):
							Running = False

					elif (event.code == "BTN_TL"):
						if (str(event.state) == "1"):
								RunningVideo = True
								msgPad = "streamon"
								print ("starting video")
					elif (event.code == "BTN_TR"):
						if (str(event.state) == "1"):
								RunningVideo = False
								# msgPad = "streamoff" 	# seems to be contraproductive

								print ("stopping video")
					elif (event.code == "BTN_START"):
						if (str(event.state) == "1"):
							msgPad = "rc -100 -100 -100 100"
							print ("starting motors")
					elif (event.code == "BTN_THUMBR 1"):
						if (str(event.state) == "1"):
							msgPad = "emergency"
					elif (event.code == "BTN_THUMBL 1"):
						if (str(event.state) == "1"):
							msgPad = "emergency"
					elif (event.code == "BTN_SELECT"):
						if (str(event.state) == "1"):
							msgPad = "emergency"

					
			if (msgPad != ""):
				if not 'rc' in msgPad:		# don't print rc messages
				# if (1):
					print (msgPad)
				msgPad = msgPad.encode(encoding="utf-8") 
				try:
					sent = sock.sendto(msgPad, tello_address)
				except Exception as e:
					print (str(e))

		
	else:
		print ("No gamepad found")
		
	print ("pad task ended")

#-----------------------------------------------------------------------------------

def video():
	global out
	global displayVideo
	global writeVideo
	global RunningVideo
	global Running

	print ("video task started")
	print (displayVideo, writeVideo)
	# wait for frame
	ret = False
	# scale down
	scale = 1
	
	while Running:
		# wait until video is started by user
		while Running and not RunningVideo: 
			time.sleep (1)
		
		if not Running:				# if video is not started at all, and user terminates the program
			print ("video task ended")
			return
		
		print ('One moment please...')
		time.sleep(3)	# give tello some time to start the video stream

		
		if (displayVideo):
			print ("opening video window")
			cv2.namedWindow('Tello')
		
		print ('opening camera feed')
		telloVideo = cv2.VideoCapture("udp://@0.0.0.0:11111")
		if (telloVideo.isOpened() == False):
			print("Unable to read camera feed")
		else:
			time.sleep(3)	# give ffmpeg some time to analyze video stream
			frame_width  = int(telloVideo.get(cv2.CAP_PROP_FRAME_WIDTH))
			frame_height = int(telloVideo.get(cv2.CAP_PROP_FRAME_HEIGHT))
			frame_fps    =     telloVideo.get(cv2.CAP_PROP_FPS)
			frame_fourcc =     telloVideo.get(cv2.CAP_PROP_FOURCC)
			print (frame_width, ' x ', frame_height, ' ', frame_fps, 'fps', ', fourcc: ', frame_fourcc)
			
			if writeVideo:
				# find a filename which doesn't yet exist
				found = False
				count = 0
				while (not found):
					filenameToWrite = 'telloVideo' + str(count).zfill(3) + '_' + args.codec + '.' + args.ext
					if (os.path.exists(filenameToWrite)):
						count = count + 1
					else:
						found = True
				
				codecString = args.codec
				while (len(codecString) < 4):		# if codecString is less than 4 characters, add blank(s)
					codecString = codecString + ' '
				fourcc = cv2.VideoWriter_fourcc(*codecString)
				print (hex(fourcc))
				out = cv2.VideoWriter(filenameToWrite, fourcc, frame_fps, (frame_width,frame_height))

			videoInterval = 1 / frame_fps
			timeNextFrame = time.time() + videoInterval
			timeStart = time.time()
			numFramesReceived = 0
			numFramesWritten = 0
			numGlitches = 0
			numSkipped = 0
			numFailed = 0

			while Running and RunningVideo: 
				# Capture frame-by-frame
				ret, frame = telloVideo.read()
				if(ret):

					numFramesReceived = numFramesReceived + 1
					now = time.time()
					if (now >= timeNextFrame): 
						timeNextFrame = timeNextFrame + videoInterval
						if (now > timeNextFrame): 				# if we missed a frame
							numGlitches = numGlitches + 1

						if writeVideo:
							out.write(frame)
							numFramesWritten = numFramesWritten + 1

						# Display the frame
						if (displayVideo):
							if (args.scale != 1.0):
								height , width , layers =  frame.shape
								new_h=int(height/args.scale)
								new_w=int(width/args.scale)
								frame = cv2.resize(frame, (new_w, new_h)) # <- resize for improved performance
							cv2.imshow('Tello',frame)
							cv2.waitKey(1)	# this is essential, otherwise cv2 won't show anything!
					else:
						numSkipped = numSkipped + 1 # we received a frame too early, so we skipped it
						
				else:
					numFailed = numFailed + 1
			
			print ('stopping video')
			timeVideo = time.time() - timeStart
			
			# When everything is done, clean up
			if writeVideo:
				out.release()
			if (displayVideo):
				cv2.destroyAllWindows()
			telloVideo.release()
			
			# do some statistics
			print ("time: ", timeVideo)
			print (numFramesReceived, "frames received, ", "%.2f" % (numFramesReceived/timeVideo), " fps")
			print (numFramesWritten,  "frames written",    "%.2f" % (numFramesWritten/timeVideo),  " fps")
			print (numGlitches, " glitches")
			print (numFailed, " frames failed")
			print (numSkipped, " frames skipped")

	print ("video task ended")
	
#-----------------------------------------------------------------------------------
print ('\r\n\r\nTello Python3 Demo.\r\n')
print ('get help with parameter -h\r\n')
print ('Steer Tello with keyboard commands or gamepad')
print ('Issue normal Tello commands like takeoff')
print ('Additional commands: ')
print ('	start (start motors without taking off), ')
print ('	video (start video), ')
print ('	oediv (stop video), ')
print ('	end   (end program)')

parser = argparse.ArgumentParser(description = "Tello Joystick Video", epilog = "Steer with keyboard commands like \"takeoff\" or with gamepad, start video with command \"video\" or with left shoulder button of gamepad")

parser.add_argument("-d", "--display", type=str, default='no', help="display video yes/no, default = no")
parser.add_argument("-s", "--scale", type=float, default=1.0, help="scale down video frame for performance reasons, default = 1.0 (don't rescale)")
parser.add_argument("-w", "--write", type=str, default='no', help="write video yes/no, default = no")
parser.add_argument("-c", "--codec", type=str, default='XVID', help="Video compression codec, default = XVID")
parser.add_argument("-e", "--ext", type=str, default='avi', help="Video file extension, default = avi")
args = parser.parse_args()

Running = True
RunningVideo = False
DataDecoded = ""
out = None
if ("Y" in args.display.upper()):
	displayVideo = True
else:
	displayVideo = False
if ("Y" in args.write.upper()):
	writeVideo = True
else:
	writeVideo = False


host = ''
# port = 9000
port = 8889
locaddr = (host,port) 


# Create a UDP socket
IpAddress = '192.168.10.1'	# hard coded. For Tello EDU, we could add ip as a a parameter
tello_address = (IpAddress, 8889)
# tello_address = (IpAddress, port)
waitForConnection (IpAddress)

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.settimeout (1)

sock.bind(locaddr)
TimeSend = 0
Rc = [0,0,0,0]


#recvThread create
recvThread = threading.Thread(target=recv)
recvThread.start()

#videoThread create
videoThread = threading.Thread(target=video)
videoThread.start()

# padThread create
padThread = threading.Thread(target=pad)
padThread.start()

msg = 'command'	# initial command to enter sdk mode

while Running: 
	if (msg == ''):
		msg = input(">")

	if 'video' in msg:		# start video
		RunningVideo = True;
		msg = 'streamon'
		
	elif 'oediv' in msg:	# "video", read backwards .... stop video
		RunningVideo = False;
		# msg = 'streamoff'		# seems to be contraproductive
		msg = ''
		
	elif 'start' in msg:
		msg = "rc -100 -100 -100 100"	# start motors

	elif 'end' in msg:	# end program
		print ('...')
		Running = False
		RunningVideo = False
		msg = ''

	if (msg != ''):
		# Send data
		msg = msg.encode(encoding="utf-8") 
		sent = sock.sendto(msg, tello_address)
		print (str(sent) + ' bytes sent')
		msg = ''

TimeShutdown = 2
print ("Will shut down in " + str(TimeShutdown) + " seconds")
time.sleep (TimeShutdown) # give recv task some time to end 
sock.close()  

exit()

