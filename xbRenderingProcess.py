# pylint: disable=E1101
# not the built-in python module
import multiprocess

import os
import importlib
import asyncio
import queue
import helpers.h
import array

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

	def __init__(self, task_queue, result_queue):
		super().__init__()
		self.taskQueue = task_queue
		self.resultQueue = result_queue
		self.currentTaskGroup = []

		self.allPossiblePlugins = self._getAllPossiblePlugins()

	# inherited from multiprocessing.Process
	def run(self):
		while True:
			# look at the task queue and see what needs to be done
			# removes task from queue
			try:
				data = self.taskQueue.get_nowait()
				# have instructions!
				self.haveInstructionsToProcess = True
				instruction = None
				if type(data) == str:
					instruction = data
				else:
					instruction = data[0]
				# there is no other data if the datatype is not a tuple
				if instruction == "setPlugin":
					# last argument is whether to create a class instance or not
					self._setPlugin(data[1], data[2])
				elif instruction == "endPlugin":
					self._endPlugin()
				elif instruction == "setResolution":
					self._setResolution(data[1], data[2])
				elif instruction == "setTime":
					self._setTime(data[1])
				elif instruction == "setValue":
					self._setValue(data[1], data[2])
				elif instruction == "render":
					self._render()
				elif instruction == "getInfo":
					self._getInfo()
				elif instruction == "SHUTDOWN":
					self._stop()
					# breaking the while loop is handled by _stop
			except queue.Empty:
				# no items to read anymore
				if self.needsToStop:
					# best time to say goodbye
					self._return("DONE")
					break
	
	# external functions (as in, will be indirectly called by an outside thread)
	def _getAllPluginSettings(self):
		pluginSettings = []
		for pluginName in self.allPossiblePlugins:
			# plugin settings should be pickleable
			pluginSettings.append((pluginName, self.allPossiblePlugins[pluginName].PLUGIN_SETTINGS))
		self._return(pluginSettings)

	# functions pertaining to the current plugin
	def _setPlugin(self, pluginName, wantInstance):
		# plugin name will be the filename without ".py"
		if self.currentPlugin is not None:
			self.endPlugin()
		self.currentPluginClass = self.allPossiblePlugins[pluginName]
		if wantInstance:
			# this makes sense when only the info is desired from the class
			# may take a long time in some cases
			self.currentPlugin = self.allPossiblePlugins[pluginName].Main()

	def _endPlugin(self):
		if self.currentPlugin is not None:
			self.currentPlugin._delete() # call the delete function
			del self.currentPlugin
			self.currentPlugin = None

	def _setResolution(self, width, height):
		self.currentPlugin.setResolution(width, height)

	def _setTime(self, timeInMilliseconds):
		self.currentPlugin.setTime(timeInMilliseconds)

	def _setValue(self, valueName, value):
		setattr(self.currentPlugin, valueName, value)
		self.currentPlugin._change_var(valueName)  # notify the plugin

	def _render(self):
		imageRender = self.currentPlugin.getImage()
		self._return(imageRender)

	def _getInfo(self):
		# returns all plugin settings as dict
		self._return(self.currentPluginClass.PLUGIN_SETTINGS)

	# internal functions
	def _return(self, value):
		# notify the main thread that an item has been returned (may not work, but I will try)
		self.resultQueue.put(value)

	def _getAllPossiblePlugins(self):
		pluginModule = importlib.import_module("plugins")
		thePlugins = {}
		for plugin in dir(pluginModule):
			if plugin.startswith("Gp"):  # yes, its a graphics plugin!
				thisPlugin = importlib.import_module("plugins." + plugin)
				if not thisPlugin.PLUGIN_SETTINGS:
					thisPlugin.PLUGIN_SETTINGS = {}  # initialize to empty dict
				thisPlugin.B_V = {  # built in variables available at runtime
					"FILE_NAME": os.path.basename(thisPlugin.__file__),
					"FILE_DIR": os.path.dirname(thisPlugin.__file__),
					"FILE_PATH": thisPlugin.__file__
				};
				thePlugins[plugin] = thisPlugin
		return thePlugins

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
	def __init__(self):
		self.instructionQueue = multiprocess.Queue()
		self.resultQueue = multiprocess.Queue()
		self.allResults = []

		# returns a multiprocessing.Process
		self.renderProcess = renderingProcess(self.instructionQueue, self.resultQueue)
		self.renderProcess.start()

		# runs function async in background
		self.loop = asyncio.get_event_loop()
		# the task itself to create, starts automatically
		self.pollTask = self.loop.create_task(self.startPolling())

	async def startPolling(self):
		# this will continue to run while results exist in the result queue
		while True:
			try:
				immidiateResult = self.resultQueue.get_nowait()
				# add to internal buffer and process later
				if immidiateResult == "DONE":
					# time to end, so quit
					break
				else:
					# it is okay, keep appending
					self.allResults.append(immidiateResult)
			except queue.Empty:
				# no items to read yet
				pass

	def pluginSetPlugin(self, pluginName, wantInstance=True):
		self.rawInstruction(("setPlugin", pluginName, wantInstance))

	def pluginEndPlugin(self):
		self.rawInstruction("endPlugin")

	def pluginSetResolution(self, width, height):
		self.rawInstruction(("setResolution", width, height))

	def pluginSetTime(self, timeInMilliseconds):
		self.rawInstruction(("setTime", timeInMilliseconds))

	def pluginSetValue(self, valueName, value):
		self.rawInstruction(("setValue", valueName, value))

	def pluginRender(self):
		self.rawInstruction("render")
		
	def rawInstruction(self, instruction):
		self.instructionQueue.put_nowait(instruction)

	def getPluginInfo(self):
		self.rawInstruction("getInfo")

	def stop(self):
		# send tuple with stop instruction
		self.rawInstruction("SHUTDOWN")
		# wait till all results are known to have been received, will block
		self.loop.run_until_complete(self.pollTask)
		# block until background process has finished, may already be done
		self.renderProcess.join()
		# returns the results, so the main program can deal with them
		return self.allResults

def createMultiCoreInterface():
	pluginInterfaces = []
	processesMillisecondsAssigned = []

	coreNum = None
	pluginName = None
	def __init__(self, coreNum, millisecondRanges, pluginName, fps):
		self.coreNum = coreNum
		self.pluginName = pluginName
		# runs function async in background
		for i in range(0, coreNum):
			self.pluginInterfaces.append(renderInterface())
			# unsigned long should be fine
			self.processesMillisecondsAssigned.append(array.array("L"))
		# the assignments for the cores
		# also, round fast because we have to do this a lot, also means that the fps is not perfect
		millisecondDelay = helpers.h.fastRound(1000 / fps)
		assignments = helpers.h.getListOfAssignmentsForCores(coreNum, millisecondRanges, millisecondDelay)
		for pair in assignments:
			# unpair first
			millisecond, coreNum = helpers.h.elegantUnpair(pair)
			# assign the millisecond to the process
			processesMillisecondsAssigned[coreNum].append(millisecond)
	def start(self):
		for coreNum in range(0, self.coreNum):
			thisRenderInterface = self.pluginInterfaces[coreNum]
			# set plugin
			thisRenderInterface.pluginSetPlugin(self.pluginName)
			millisecondsToAssign = self.processesMillisecondsAssigned[coreNum]
			for millisecond in millisecondsToAssign:
				# assign instructions to render for each process
				thisRenderInterface.pluginSetTime(millisecond)
				thisRenderInterface.pluginRender()
	def waitForEnd():
		# TODO
		pass