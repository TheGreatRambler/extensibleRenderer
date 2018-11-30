import ctypes
from pywinauto.application import Application
from mss import mss
from PIL import Image

class Main():
	def __init__(self, command):
		# open gui with command
		self.appInstance = Application(backend="win32").start(command)
		# get the main/top window
		self.mainWindow = self.appInstance.top_window()
		# wait until CPU usage is lower than 5%
		self.appInstance.wait_cpu_usage_lower(threshold=5)
		# get screen size so window can be outside screen (TODO need to implement)
		# just go for a massive value (last value is repaint ant 2 Nones are width and height)
		self.appLocation = [1800, 950]
		self.mainWindow.move_window(self.appLocation[0], self.appLocation[1], None, None, False)
		"""
		screenClientRect = self.mainWindow.client_rect()
		# gets client area (minus toolbars)
		self.windowView = {
			"top": self.appLocation[1],
			"left": self.appLocation[0],
			"width": screenClientRect.width(),
			"height": screenClientRect.height(),
			"mon": 0
		}
		self.screenshotInstance = mss()
		print(self.windowView)	
		"""
	def getScreenshot(self):
		# returns pil image of main window
		return self.mainWindow.capture_as_image()
		
Main("notepad.exe").getScreenshot().save("notepad.png")