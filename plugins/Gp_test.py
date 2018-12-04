from PIL import Image
import pexpect
import pexpect.popen_spawn
import lz4
import lz4.frame
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
 "RENDER_IN_ORDER": True, # the frames must be rendered in order because they affect one another
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
	mainColor = None
	dataFromJavascript = None
	nodeServerAddress = None
	def __init__(self):
		# cross platform version of pexpect
		javascriptFileCommand = "node " + os.path.join(os.path.dirname(os.path.realpath(__file__)), "dwitter", "main.js")
		self.inMemoryLogHistory = onWriteMemoryFile(self.onCommandWrite) # simple on-write memory object
		self.canvasInstance = pexpect.popen_spawn.PopenSpawn(cmd=javascriptFileCommand, logfile=self.inMemoryLogHistory)
		self.setup()

	def _delete(self):
		self.canvasInstance.kill(signal.SIGTERM) # close node instance

	def _change_var(self, variableName):
		self.getImage().save("test.png")


	def onCommandWrite(self, line):
		if line.startswith("D"):
			# remove D so the data is valid
			self.dataFromJavascript = line[1:] # removes the "D"

	def getImage(self):
		self.canvasInstance.sendline("render")
		# when next appears, the rendering has finished
		self.canvasInstance.expect_exact("next")
		# listen on server to find the data
		imageRequest = requests.get(self.nodeServerAddress + "/file")
		# will have decoded image
		imageRGBAData = Image.frombytes("RGBA", (1920, 1080), lz4.frame.decompress(data=imageRequest.content))
		return imageRGBAData

	def setup(self):
		# listen for start (blocking)
		self.canvasInstance.expect_exact("started")
		# set the dweet number
		self.canvasInstance.sendline("setDweet 888")
		# wait till we can accept another command to return
		self.canvasInstance.expect_exact("next")
		# send command to set to beginning time
		self.canvasInstance.sendline("time 0")
		# wait till we can accept another command
		self.canvasInstance.expect_exact("next")
		# get address
		self.canvasInstance.sendline("address")
		self.canvasInstance.expect_exact("next")
		# we now have the server address
		self.nodeServerAddress = self.dataFromJavascript
	
	def setResolution(self, width, height):
		pass
	
	def setTime(self, time):
		# send command
		self.canvasInstance.sendline("time " + time)
		# wait for it to finish
		self.canvasInstance.expect_exact("next")
	