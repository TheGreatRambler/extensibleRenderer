from PIL import Image

import pexpect
import pexpect.popen_spawn
import lz4
import lz4.frame
import requests
# use for fake file


import subprocess
import os
import signal
import sys
import io
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
		# redirect all outputs to in memory thing
		self.redirectCanvasInstanceToNothing()
		self.setup()

	def _delete(self):
		self.canvasInstance.kill(signal.SIGKILL) # kill node instance completely

	def _change_var(self, variableName):
		pass

	def onCommandWrite(self, line):
		if line.startswith("D"):
			# remove D so the data is valid
			self.dataFromJavascript = line[1:] # removes the "D"

	def redirectCanvasInstanceToNothing(self):
		# monkey patch the instance
		"""
		self.canvasInstance.proc.stdout = io.BytesIO()
		self.canvasInstance.proc.stdin = io.BytesIO()
		self.canvasInstance.proc.stderr = io.BytesIO()
		"""

	def getImagesInOrder(self, milliRange, skip):
		# there is no getImage for this kind of rendering function
		# there is also no setTime
		# render all in a row
		self.canvasInstance.sendline("render " + str(milliRange[0]) + " " + str(milliRange[1]) + " " + str(skip))
		# when next appears, the rendering has finished
		self.canvasInstance.expect_exact("next")
		# returns byte array
		allImageRequests = requests.get(self.nodeServerAddress + "/file")
		# the size is the width times the height
		sizeOfPixelBlock = self.width * self.height
		arrayOfPixelData = [allImageRequests[i:i+sizeOfPixelBlock] for i in range(0, len(allImageRequests), sizeOfPixelBlock)]
		images = [Image.frombytes("RGBA", (self.width, self.height), pixels) for pixels in arrayOfPixelData]
		print(len(images))
		return images

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
		# set size to default value
		self.setResolution(1920, 1080)
	
	def setResolution(self, width, height):
		self.width = width
		self.height = height
		# set size
		self.canvasInstance.sendline("setSize " + str(width) + " " + str(height))
		# wait for end
		self.canvasInstance.expect_exact("next")