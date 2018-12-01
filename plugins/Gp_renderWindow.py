import win32gui
import win32ui
import keyboard
import ctypes
import pywinauto
from pywinauto.application import Application
from PIL import Image
import subprocess
import os
import time
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
		# call command separately of pywinauto (redirection to DEVNULL prevents output)
		self.DEVNULL = open(os.devnull, 'w')
		self.process = subprocess.Popen(command, stdout=self.DEVNULL)
		# try alt-enter
		self.simulateAltEnter()
		# open command window with existing command's PID
		self.appInstance = Application(backend="win32").connect(process=self.process.pid)
		# get the main/top window
		self.mainWindow = self.appInstance.top_window()
		# wait until the main window is active (maybe it should be enabled)
		self.mainWindow.wait("enabled")
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

	def kill(self):
		self.breakdownScreenshotBitmap()
		# kills given the pid
		subprocess.Popen("TASKKILL /F /PID {pid} /T".format(pid=self.process.pid), stdout=self.DEVNULL)

	def simulateAltEnter(self):
		keyboard.send("alt+enter")
		
instance = Main(r"C:\Users\aehar\Desktop\Windows\GreekWarSaver.exe")
instance.getScreenshot().save("thing1.png")
instance.getScreenshot().save("thing2.png")
instance.kill()