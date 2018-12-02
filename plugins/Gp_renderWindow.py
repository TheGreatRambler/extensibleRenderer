import win32gui
import win32ui
import ctypes
import pywinauto
from pywinauto.application import Application
from pywinauto import Desktop
from PIL import Image
import subprocess
import os
import psutil
# windows only solution
# the way to get all applications (including jars and programs that start through the command line) is
# by starting cmd.exe with this then manually putting in the command needed, listen for further windows,
# and designate them as the main window

class Main():
	# may need launch4j or jar2exe for jar files
	# if apps are reported as not having windows... good luck!
	def __init__(self, command):
		# we don't want cruft
		pywinauto.actionlogger.disable()
		# setup the application
		# Output will say wether it failed or succeeded
		applicationCreated = self.makeWorkingAppInstance(command)
		# get the main/top window
		# if application instance was not created, use the Desktop api
		self.getMainWindow(command, applicationCreated)
		# wait until the main window is active (maybe it should be enabled)
		self.mainWindow.wait("visible")
		# get screen size so window can be outside screen (TODO need to implement)
		# just go for a massive value (last value is repaint ant 2 Nones are width and height)
		self.appLocation = [3000, 3000]
		self.mainWindow.move_window(self.appLocation[0], self.appLocation[1], None, None, False)
		# not documented, but the HWND handle is a property on the class instance of the window
		self.hwnd = int(self.mainWindow.handle) # convert to long to pass as HWND value
		self.setupScreenshotBitmap() # needs to be done to set up the screenshots
	def getScreenshot(self):
		# returns image of main window client area
		didSucceed = ctypes.windll.user32.PrintWindow(self.hwnd, self.saveDC.GetSafeHdc(), 1)
		if didSucceed:
			bmpinfo = self.saveBitMap.GetInfo()
			bmpstr = self.saveBitMap.GetBitmapBits(True)
			im = Image.frombuffer("RGB", (bmpinfo["bmWidth"], bmpinfo["bmHeight"]), bmpstr, 'raw', 'BGRX', 0, 1)
			return im

	def setupScreenshotBitmap(self):
		# https://stackoverflow.com/questions/19695214/python-screenshot-of-inactive-window-printwindow-win32gui
		left, top, right, bot = win32gui.GetWindowRect(self.hwnd)
		w = right - left
		h = bot - top

		self.hwndDC = win32gui.GetWindowDC(self.hwnd)
		self.mfcDC  = win32ui.CreateDCFromHandle(self.hwndDC)
		self.saveDC = self.mfcDC.CreateCompatibleDC()

		self.saveBitMap = win32ui.CreateBitmap()
		self.saveBitMap.CreateCompatibleBitmap(self.mfcDC, w, h)

		self.saveDC.SelectObject(self.saveBitMap)

	def breakdownScreenshotBitmap(self):
		win32gui.DeleteObject(self.saveBitMap.GetHandle())
		self.saveDC.DeleteDC()
		self.mfcDC.DeleteDC()
		win32gui.ReleaseDC(self.hwnd, self.hwndDC)

	def findProcessesByName(self, name):
		ls = []
		for p in psutil.process_iter():
			# check if either the full path or just the filename has been created
			if p.name() == name or p.name() == os.path.basename(name):
				ls.append(p.pid)
			'''
			name_, exe, cmdline = "", "", []
			try:
				name_ = p.name()
				cmdline = p.cmdline()
				exe = p.exe()
				print(name_, cmdline, exe)
			except (psutil.AccessDenied, psutil.ZombieProcess):
				pass
			except psutil.NoSuchProcess:
				continue
			if name == name_ or cmdline[0] == name or os.path.basename(exe) == name:
				ls.append(p.pid)
			'''
		return ls

	def makeWorkingAppInstance(self, commandList):
		# helper pipe to flush popen
		self.DEVNULL = open(os.devnull, 'w')
		# start the instance now
		# sill be used many times throughout this function
		self.appInstance = Application(backend="win32")
		# first things first, lets try to create one from scratch
		self.pid = subprocess.Popen(commandList, stdout=self.DEVNULL).pid
		self.appInstance.connect(process=self.pid)
		if len(self.appInstance.windows()) != 0:
			# the app we created has some windows, we are done
			self.usedExisting = True
			# It worked
			return True
		else:
			# We have to connect to an existing one
			# kill the one we created, it is pointless
			self.killPid(self.pid)
			# find possible processes to use
			possibleProcesses = self.findProcessesByName(commandList[0])
			if len(possibleProcesses) == 0:
				# goodness, the app is not running anywhere and it has no children
				# this is a disaster
				return False
			else:
				# check to see if it worked
				foundWorkingOne = False
				pidToUse = 0 # just a dummy number
				for pid in possibleProcesses:
					self.appInstance.connect(process=pid)
					if len(self.appInstance.windows()) != 0:
						# wow, this process has windows! Lets use it!
						foundWorkingOne = True
						pidToUse = pid
						# we have what we need, lets get out of here
						break
				if foundWorkingOne:
					# yay, register them. The application is already connected
					self.pid = pidToUse
					self.usedExisting = True
					return True
				else:
					# I dont know what to do? There are places where this process is running
					# But none of them have windows
					return False

	def getMainWindow(self, commandList, getAppWorked):
		if getAppWorked is True:
			self.mainWindow = self.appInstance.top_window()
		else:
			# start app seperately
			self.usedExisting = False
			self.pid = subprocess.Popen(commandList, stdout=self.DEVNULL).pid
			# gets executable without extension
			# most apps follow this pattern
			self.mainWindow = Desktop(backend="win32").window(best_match=commandList[0].split(".")[0])

	def kill(self):
		self.breakdownScreenshotBitmap()
		# kills given the pid
		if not self.usedExisting:
			# dont want to kill a process that was already running
			self.killPid(self.pid)
		else:
			# maybe the old window should be restored?
			pass

	def killPid(self, pid):
		subprocess.Popen("TASKKILL /F /PID {pid} /T".format(pid=pid), stdout=self.DEVNULL)
		
instance = Main([r"C:\Windows\ImmersiveControlPanel\SystemSettings.exe"])
instance.getScreenshot().save("thing1.png")
instance.kill()