from PIL import Image
from pyppeteer import launch
import websockets
from cbor import loads as ccborloads

import os
import asyncio
import socket
from contextlib import closing

PLUGIN_SETTINGS = {
 "NAME": "Dwitter",
 "DESCRIPTION": "Dwitter generator",
 "CATEGORY": "Etc",
 "RENDER_IN_ORDER": True, # the frames must be rendered in order because they affect one another
 "PYTHON_VERSION": 3.6 # what is the minimum version of python that will work
}


def getDwitterHtmlPage():
	# concate this directory and the path to the file
	htmlFileString = None
	with open(os.path.realpath(os.path.join(os.path.dirname(__file__), "dwitter", "main.html")), "r") as htmlFile:
		htmlFileString = htmlFile.read()
	return htmlFileString

def getAssetPath(filename):
	return os.path.realpath(os.path.join(os.path.dirname(__file__), "dwitter", filename))

def findFreePort():
	with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as s:
		s.bind(("localhost", 0))
		return s.getsockname()[1]

class Main():
	browser = None
	mainPage = None

	run = asyncio.get_event_loop().run_until_complete

	width = None
	height = None

	port = None
	def __init__(self):
		self.run(self.getStarted())
		# set default
		self.setResolution(1920, 1080)
		self.setDweet(5879)

	async def getStarted(self):
		self.browser = await launch(headless=False)
		self.mainPage = await self.browser.newPage()
		await self.mainPage.addScriptTag(path=getAssetPath("cbor.js"))
		# set html page from string
		await self.mainPage.setContent(getDwitterHtmlPage())
		await self.mainPage.exposeFunction("print", lambda i: print(i))

		await self.setPort()
		await self.startServer()
		await self.startWebsocketClient()

	async def startServer(self):
		return websockets.serve(self.connectionHandler, "localhost", self.port)

	async def connectionHandler(self, websocket, path):
		self.dataWebsocket = websocket

	async def startWebsocketClient(self):
		await self.runFunctionOnPage("""
			function() {{
				startClient();
			}}
		""")

	async def runFunctionOnPage(self, functionString):
		return await self.mainPage.evaluate(functionString)

	def setResolution(self, width, height):
		self.width = width
		self.height = height
		self.run(self.runFunctionOnPage("""
			function() {{
				setSize({0},{1});
			}}
		""".format(width, height)))

	def getImagesInOrder(self, start, end):
		self.run(self.runFunctionOnPage("""
			function() {{
				renderFromStartToEnd({0},{1});
			}}
		""".format(start, end)))
		# block while recieving message from client, which will take a long time
		# the message should be an array of bytearrays, but that is up for contention
		images = ccborloads(self.run(self.dataWebsocket.recv()))
		images = [Image.frombytes("RGBA", (self.width, self.height), pixels) for pixels in images]
		print(len(images))
		return images

	def setDweet(self, dweetNum):
		self.run(self.runFunctionOnPage("""
			function() {{
				setDweet({0});
			}}
		""".format(dweetNum)))

	async def setPort(self):
		self.port = findFreePort()
		await self.runFunctionOnPage("""
			function() {{
				setPort({0});
			}}
		""".format(self.port))