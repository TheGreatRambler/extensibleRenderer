from PIL import Image
import pexpect
import pexpect.popen_spawn
import lz4
import requests

import subprocess
import os
import signal
import io
import sys
from helpers.h import onWriteMemoryFile

PLUGIN_SETTINGS = {
 "NAME": "Test",
 "DESCRIPTION": "Just a test",
 "CATEGORY": "Etc",
 "REQUIREMENTS": ["pexpect"], # list of requirements (not needed now)
 "VARIABLES": {
  "mainColor": {
   "NAME": "Main Color",
   "DESCRIPTION": "Choose the main color to show",
   "TYPE": "COLOR #FF7F50"
  }
 }
}

# skeleton plugin
class Main():
	def __init__(self):
		self.mainColor = None # init it
		self.dataFromJavascript = None
		# cross platform version of pexpect
		javascriptFileCommand = "node " + os.path.join(os.path.dirname(os.path.realpath(__file__)), "dwitter", "main.js")
		self.inMemoryLogHistory = onWriteMemoryFile(self.onCommandWrite) # simple on-write memory object
		self.canvasInstance = pexpect.popen_spawn.PopenSpawn(cmd=javascriptFileCommand, logfile=self.inMemoryLogHistory)
		# listen for start (blocking)
		self.canvasInstance.expect_exact("started")
		# send command to set to beginning
		self.canvasInstance.sendline("time 0")
		# wait till we can accept another command to return
		self.canvasInstance.expect_exact("next")

	def onDelete(self):
		self.canvasInstance.kill(signal.SIGTERM) # close node instance

	def _change_var(self, variableName):
		self.canvasInstance.sendline("render")
		# when next appears, the rendering has finished
		self.canvasInstance.expect_exact("next")
		# listen on server to find the data

	def onCommandWrite(self, line):
		if line.startswith("D"):
			self.dataFromJavascript = line
	
	def renderNextFrame(self, delta):
		pass
	
	def setResolution(self, width, height):
		pass
	
	def setTime(self, time):
		pass
	