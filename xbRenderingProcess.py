# pylint: disable=E1101
# not the built-in python module
import multiprocess

import os
import importlib
import asyncio
import queue
import helpers.h
import array
import time
import psutil

# for type checking
from builtins import str

import secrets

import SETTINGS

# experimental implementation that is on a different process


# there is no checking to make sure the plugin has started, so start beforehand
# process implementation from https://pymotw.com/2/multiprocessing/communication.html
# process is entirely synchronous, but multiple instances are created, 1 per logical core
class renderingProcess(multiprocess.Process):
	currentPlugin = None
	currentPluginClass = None
	allPossiblePlugins = None

	taskQueue = None
	resultQueue = None
	needsToStop = False

	currentTime = 0

	def __init__(self, task_queue, result_queue, limitCpu):
		super().__init__()

		if limitCpu:
			# lower priority to help cpu usage
			p = psutil.Process(os.getpid())
			if os.name == "nt":
				# we are on windows
				p.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
			else:
				# we are on a linux deritive
				p.nice(19)

		self.taskQueue = task_queue
		self.resultQueue = result_queue
		self.currentTaskGroup = []

	# inherited from multiprocessing.Process
	def run(self):
		while True:
			# look at the task queue and see what needs to be done
			# removes task from queue
			try:
				recievedData = self.taskQueue.get_nowait()
				# have instructions!
				# set lock to let manager know that we are processing
				self.haveInstructionsToProcess = True
				# first element is always hash of instruction
				instructionHash = recievedData[0]
				# second is the instruction
				instruction = recievedData[1]
				# all elements but first two
				data = recievedData[2:]
				# there is no other data if the datatype is not a tuple
				if instruction == "setPlugin":
					# last argument is whether to create a class instance or not
					self._setPlugin(data[0], data[1])
				elif instruction == "endPlugin":
					self._endPlugin()
				elif instruction == "setResolution":
					self._setResolution(data[0], data[1])
				elif instruction == "setTime":
					self._setTime(data[0])
				elif instruction == "setValue":
					self._setValue(data[0], data[1])
				elif instruction == "render":
					self._render(instruction)
				elif instruction == "renderInOrder":
					# bulk render
					self._renderInOrder(instruction, data[0], data[1], data[2])
				elif instruction == "getInfo":
					self._getInfo(instruction)
				elif instruction == "SHUTDOWN":
					self._stop()
					# breaking the while loop is handled by _stop
				self._return(("doneInstruction", instructionHash))
				# release lock
			except queue.Empty:
				# no items to read anymore
				if self.needsToStop:
					# best time to say goodbye
					self._return(("DONE",))
					break

	# functions pertaining to the current plugin
	def _setPlugin(self, pluginName, wantInstance):
		# plugin name will be the filename without ".py"
		if self.currentPlugin is not None:
			self.endPlugin()
		self.currentPluginClass = self._importPlugin(pluginName)
		if wantInstance:
			# this makes sense when more than the info is wanted
			# may take a long time in some cases
			self.currentPlugin = self._importPlugin(pluginName).Main()

	def _endPlugin(self):
		if self.currentPlugin is not None:
			self.currentPlugin._delete() # call the delete function
			del self.currentPlugin
			self.currentPlugin = None

	def _setResolution(self, width, height):
		self.currentPlugin.setResolution(width, height)

	def _setTime(self, timeInMilliseconds):
		self.currentTime = timeInMilliseconds
		self.currentPlugin.setTime(timeInMilliseconds)

	def _setValue(self, valueName, value):
		setattr(self.currentPlugin, valueName, value)
		self.currentPlugin._change_var(valueName)  # notify the plugin

	def _render(self, name):
		# render like normal
		imageRender = self.currentPlugin.getImage()
		# pil images are pickleable
		self._return((name, self.currentTime, imageRender))

	def _renderInOrder(self, name, start, end, skip):
		# render in order as bulk
		allRenderings = self.currentPlugin.getImagesInOrder((start, end), skip)
		index = 0
		for renderTime in range(start, end + 1, skip):
			# pil images are pickleable
			self._return((name, renderTime, allRenderings[index]))
			index += 1

	def _getInfo(self, name):
		# returns all plugin settings as dict
		self._return((name, self.currentPluginClass.PLUGIN_SETTINGS))

	# internal functions
	def _return(self, value):
		# notify the main thread that an item has been returned (may not work, but I will try)
		self.resultQueue.put(value)

	def _importPlugin(self, pluginName):
		plugin = importlib.import_module("plugins." + pluginName)
		# create the PLUGIN_SETTINGS
		if not hasattr(plugin, "PLUGIN_SETTINGS"):
			plugin.PLUGIN_SETTINGS = {}  # initialize to empty dict
		# built in variables available at runtime
		plugin.B_V = {
			"FILE_NAME": os.path.basename(plugin.__file__),
			"FILE_DIR": os.path.dirname(plugin.__file__),
			"FILE_PATH": plugin.__file__
		}
		return plugin

	def _stop(self):
		# all that is needed: now the process will stop on its own
		self.needsToStop = True

# the main class to be created
# should be called with asyncio, because it polls async
class renderInterface():
	resultQueueEmpty = False

	instructionQueue = None
	resultQueue = None

	allResults = None

	renderProcess = None

	info = None

	pause = False

	verbose = False
	def __init__(self, verbose):
		self.instructionQueue = multiprocess.Queue()
		self.resultQueue = multiprocess.Queue()
		self.allResults = []
		self.verbose = verbose

		# returns a multiprocessing.Process
		self.renderProcess = renderingProcess(self.instructionQueue, self.resultQueue, True)
		self.renderProcess.name = "renderProcess" + secrets.token_urlsafe(5)
		self.renderProcess.start()

		# runs function async in background
		self.loop = asyncio.get_event_loop()
		# the task itself to create, starts automatically
		self.pollTask = self.loop.create_task(self.startPolling())

	async def startPolling(self):
		# this will continue to run while results exist in the result queue
		while True:
			# sync instruction is being used
			if not self.pause:
				try:
					immidiateResult = self.resultQueue.get_nowait()
					# add to internal buffer and process later
					if immidiateResult[0] == "DONE":
						# time to end, so quit
						break
					else:
						# it is okay, keep appending
						self._addResult(immidiateResult)
				except queue.Empty:
					# no items to read yet
					pass

	def pluginSetPlugin(self, pluginName, wantInstance=True):
		self.rawInstruction(("setPlugin", pluginName, wantInstance))
		info = self.rawInstructionSync("getInfo")
		# merge recieved info with default
		self.info = {**SETTINGS.defaultSettings, **info[1]}
		return self

	def pluginEndPlugin(self):
		self.rawInstruction("endPlugin")
		return self

	def pluginSetResolution(self, width, height):
		self.rawInstruction(("setResolution", width, height))
		return self

	def pluginSetTime(self, timeInMilliseconds):
		# is not used for bulk render
		self.rawInstruction(("setTime", timeInMilliseconds))
		return self

	def pluginSetValue(self, valueName, value):
		self.rawInstruction(("setValue", valueName, value))
		return self

	def pluginRender(self):
		self.rawInstruction("render")
		return self

	def pluginRenderInOrder(self, start, end, skip):
		# bulk render
		self.rawInstruction(("renderInOrder", start, end, skip))
		
	def rawInstruction(self, instruction):
		# create random hash for the instruction
		instructionHash = secrets.token_urlsafe(26)
		if isinstance(instruction, str):
			instructionHash += instruction
			# need comma so python knows its a tuple
			# convert to tuple
			self.instructionQueue.put_nowait((instructionHash,) + (instruction,))
		else:
			instructionHash += instruction[0]
			# need comma so python knows its a tuple
			self.instructionQueue.put_nowait((instructionHash,) + instruction)
		return instructionHash

	def rawInstructionSync(self, instruction):
		self.pause = True
		instructionHash = self.rawInstruction(instruction)
		# purposely block
		haveGotCurrent = False
		valueToReturn = None
		# block while searching
		while not haveGotCurrent:
			value = self.resultQueue.get()
			# yes! both things match
			# check length because the length may be 1
			if len(value) == 2 and value[0] == "doneInstruction" and value[1] == instructionHash:
				haveGotCurrent = True
				# get the last result, it was the right one!
				valueToReturn = self.getLastResult()
			else:
				# just pass it on
				self._addResult(value)
		self.pause = False
		return valueToReturn

	def getPluginInfo(self):
		self.rawInstruction("getInfo")
		return self
	
	def getMostRecentResult(self):
		return self.allResults[-1]

	def _addResult(self, result):
		self.allResults.append(result)
	
	def getLastResult(self):
		return self.allResults[-1]

	def stop(self):
		# send tuple with stop instruction
		self.rawInstruction("SHUTDOWN")
		# wait till all results are known to have been received, will block
		self.loop.run_until_complete(self.pollTask)
		# block until background process has finished, may already be done
		self.renderProcess.join()
		# returns the results, so the main program can deal with them
		return self

	def getResults(self):
		return self.allResults

	def _log(self, item):
		if self.verbose:
			print(item)

class createMultiCoreInterface():
	pluginInterfaces = []
	processesMillisecondsAssigned = []

	coreNum = None
	pluginName = None

	renderInOrder = False
	def __init__(self, coreNum, millisecondRanges, pluginName, fps):
		if renderInterface(False).pluginSetPlugin(pluginName, False).stop().info["RENDER_IN_ORDER"] is False:
			# YAY, we can multiprocess!
			self.coreNum = coreNum
			self.renderInOrder = False
		else:
			# Well, thats boring, we have to do one process
			self.coreNum = 1
			self.renderInOrder = True
		self.pluginName = pluginName
		# runs function async in background
		for core in range(0, self.coreNum):
			interface = renderInterface(False)
			# assign the core number so it can be used later
			interface._core = core
			self.pluginInterfaces.append(interface)
			# unsigned long should be fine
			self.processesMillisecondsAssigned.append(array.array("L"))
		# the assignments for the cores
		# only use millisecondOffset for renderInOrder, otherwise use better way
		self.millisecondOffset = helpers.h.fastFloor(1000 / fps)
		assignments = helpers.h.getListOfAssignmentsForCores(self.coreNum, millisecondRanges, 1000 / fps)
		currentMillisecond = 0
		for index in range(len(assignments)):
			if index % 2 == 0:
				# the index is even, so it is a millisecond
				currentMillisecond = assignments[index]
			else:
				# it is odd, so it is a core number
				# assign the millisecond to the process
				self.processesMillisecondsAssigned[assignments[index]].append(currentMillisecond)
	def start(self):
		for coreNum in range(0, self.coreNum):
			thisRenderInterface = self.pluginInterfaces[coreNum]
			# set plugin
			thisRenderInterface.pluginSetPlugin(self.pluginName)
			millisecondsToAssign = self.processesMillisecondsAssigned[coreNum]
			if self.renderInOrder:
				# well, all for being multiprocess, we have to fallback to being linear
				# we know there is one core, so this is fine
				# we have to get the last and first millisecond in the array
				firstMillisecond = min(millisecondsToAssign)
				lastMillisecond = max(millisecondsToAssign)
				# bulk render
				thisRenderInterface.pluginRenderInOrder(firstMillisecond, lastMillisecond, self.millisecondOffset)
			else:
				for millisecond in millisecondsToAssign:
					# assign instructions to render for each process
					thisRenderInterface.pluginSetTime(millisecond).pluginRender()
	def waitForEnd(self):
		allResults = []
		for plugin in self.pluginInterfaces:
			results = plugin.stop().getResults()
			# remove all results not pertaining to rendering
			# also, remove "render" in beginning of tuple
			if self.renderInOrder:
				# no need to check millisecond number
				allResults.extend([x[1:] for x in results if (x[0] == "render")])
			else:
				# we need to check the millisecond number because frames were rendered in order
				# so some unneccesary frames were rendered
				millsAssigned = self.processesMillisecondsAssigned[plugin._core]
				# check if the millisecond was assigned
				allResults.extend([x[1:] for x in results if (x[0] == "render" and x[1] in millsAssigned)])
		# TODO make it better
		# returns an array with millisecond and image render
		return allResults