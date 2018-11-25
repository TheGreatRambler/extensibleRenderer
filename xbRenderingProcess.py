import asyncio

# there is no checking to make sure the plugin has started, so start beforehand
class renderingProcess():
	currentPlugin = None
	def setPlugin(self, plugin):
		if self.currentPlugin is not None:
			self.endPlugin()
		self.currentPlugin = plugin.Main()

	def endPlugin(self):
		if self.currentPlugin is not None:
			self.currentPlugin._delete() # call the delete function
			del self.currentPlugin
			self.currentPlugin = None

	def setResolution(self, width, height):
		self.currentPlugin.setResolution(width, height)

	def setTime(self, timeInMilliseconds):
		self.currentPlugin.setTime(timeInMilliseconds)

	def setValue(self, valueName, value):
		setattr(self.currentPlugin, valueName, value)
		self.currentPlugin._change_var(valueName)  # notify the plugin)

	def render(self, doneCallback):
		pass


