import win32gui
import win32ui
import ctypes
import pywinauto
from pywinauto.application import Application
from PIL import Image

# windows only solution
# the way to get all applications (including jars and programs that start through the command line) is
# by starting cmd.exe with this then manually putting in the command needed, listen for further windows,
# and designate them as the main window

class Main():
	# may need launch4j or jar2exe for jar files
	def __init__(self, command):
		# we don't want cruft
		pywinauto.actionlogger.disable()
		# open gui with command
		self.appInstance = Application(backend="win32").start(command)
		# get the main/top window
		# might have to get out of fullscreen, alt-enter is good for this
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

	def closeApplication(self):
		pass
		
Main(r"notepad.exe").getScreenshot().save("thing.png")