import multiprocessing
import os
import importlib
import asyncio
import queue

# experimental implementation that is on a different thread


# there is no checking to make sure the plugin has started, so start beforehand
# thread implementation from https://pymotw.com/2/multiprocessing/communication.html
class renderingProcess(multiprocessing.Process):
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

		self.allPossiblePlugins = self._getAllPossiblePlugins()

	# inherited from multiprocessing.Process
	def run(self):
		while self.needsToStop is False:
			# look at the task queue and see what needs to be done
			# removes task from queue
			data = self.taskQueue.get()
			instruction = data[0]
			if instruction == "setPlugin":
				self._setPlugin(data[1]) # pass plugin object, maybe?
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
			elif instruction == "SHUTDOWN":
				self._clearAllQueues()
				# simply break the while loop
				break
	
	# external functions (as in, will be indirectly called by an outside thread)
	def _getAllPluginSettings(self):
		pluginSettings = []
		for pluginName in self.allPossiblePlugins:
			# plugin settings should be pickleable
			pluginSettings.append((pluginName, self.allPossiblePlugins[pluginName].PLUGIN_SETTINGS))
		self._return(pluginSettings)

	# functions pertaining to the current plugin
	def _setPlugin(self, pluginName):
		# plugin name will be the filename without ".py"
		if self.currentPlugin is not None:
			self.endPlugin()
		self.currentPluginClass = self.allPossiblePlugins[pluginName]
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
				}
				thePlugins[plugin] = thisPlugin
		return thePlugins

	def _clearAllQueues(self):
		# signal that both queues will be closed after all items are removed
		self.taskQueue.close()
		self.resultQueue.close()
		# prevent queues from waiting for background thread
		#self.instructionQueue.cancel_join_thread()
		#self.resultQueue.cancel_join_thread()
		try:
			while True:
				self.taskQueue.get_nowait()
		except queue.Empty:
			try:
				while True:
					self.resultQueue.get_nowait()
			except queue.Empty:
				# end the function after all items are removed from both queues
				pass

class renderInterface():
	needsToStop = False

	instructionQueue = None
	resultQueue = None

	renderProcess = None
	def __init__(self):
		self.instructionQueue = multiprocessing.Queue()
		self.resultQueue = multiprocessing.Queue()

		self.renderProcess = renderingProcess(self.instructionQueue, self.resultQueue)
		self.renderProcess.start()

		asyncio.run(self.startPolling())

	async def startPolling(self):
		while needsToStop is False:
			try:
				immidiateResult = self.resultQueue.get_nowait()
				# process result
			except queue.Empty:
				# no items to read yet
				pass

	def stop(self):
		# send tuple with stop instruction
		self.instructionQueue.put(("SHUTDOWN"))
		self.needsToStop = True
		# block until background process has finished
		self.renderProcess.join()



