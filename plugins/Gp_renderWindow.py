import ctypes
import pywinauto
from pywinauto.application import pyWinAutoApp
import mss

class Main():
	def __init__(self, command):
		# open gui with command
		self.appInstance = pyWinAutoApp(backend="win32").start(command)
		# wait until started and visible
		self.appInstance.wait("visible")
		# get the main/top window
		self.mainWindow = self.appInstance.top_window()
		# get screensize so window can be outside screen (TODO need to implement)
		# just go for a massive value (last value is repaint ant 2 nones are width and height)
		self.mainWindow.move_window(3000, 3000, None, None, False)
		self.screenshotInstance = mss()
		screenClientRect = self.mainWindow.client_rect()
		# gets client area (minus toolbars)
		self.windowView = {"top": screenClientRect.top, "left": screenClientRect.left, "width": screenClientRect.width(), "height": screenClientRect.height()}
	def getScreenshot():
		# returns pil image
		screenshot = self.screenshotInstance.grab(self.windowView)
		return Image.frombytes("RGB", screenshot.size, screenshot.bgra, "raw", "BGRX")
		
