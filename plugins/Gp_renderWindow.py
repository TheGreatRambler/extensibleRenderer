import ctypes
import pywinauto
from pywinauto.application import pyWinAutoApp

class Main():
	def __init__(self, command):
		self.appInstance = pyWinAutoApp(backend="win32").start(command)
		self.appInstance.wait("visible")
		self.mainWindow = self.appInstance.top_window()
	def moveAppWindows(self, handle, x, y):
		# last argument is wether to repaint, not now though
		ctypes.windll.user32.MoveWindow(handle, 0, 0, 760, 500, False)
