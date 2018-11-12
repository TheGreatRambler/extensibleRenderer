# pylint: disable=E1101

import wx
import wx.lib.scrolledpanel as scrolled

import helpers.h as help

NO_DESCRIPTION_LABEL_TEXT = ""


class getPluginMenu(wx.BoxSizer):
	def __init__(self, plugins, mainPanel):

		self.mainPanel = mainPanel

		wx.BoxSizer.__init__(self, orient=wx.VERTICAL)
		self.plugins = plugins
		self.lastPluginGui = None

		# very important, the instance of the plugin that is running
		self.currentPluginInstance = None

		#self.Bind(wx.EVT_ICONIZE, self.onMinimize)
		#self.Bind(wx.EVT_CLOSE, self.onClose)

		self.pluginSizer = self.getPluginChoiceSizer(parent=mainPanel)
		self.pluginInfoSizer = self.getPluginInfoSizer(parent=mainPanel)

		self.Add(self.pluginSizer, 1, wx.EXPAND, 0)
		self.Add(self.pluginInfoSizer, 3, wx.EXPAND, 0)

		self.createPluginForms()  # create the forms so they can be opened
		self.refresh()

	def getPluginChoiceSizer(self, parent):
		self.pluginTree = wx.TreeCtrl(parent=self.mainPanel, id=wx.ID_ANY, style=wx.TR_HAS_BUTTONS)
		self.setTreeHierarchy(tree=self.pluginTree)

		self.pluginTree.Bind(wx.EVT_TREE_SEL_CHANGED, self.openPlugin)

		return self.pluginTree

	def getPluginInfoSizer(self, parent):
		self.pluginInfoSizerSizer = wx.BoxSizer(wx.VERTICAL)
		#for now, nothing
		return self.pluginInfoSizerSizer

	def createPluginForms(self):
		for plugin in self.plugins:
			pluginFuncs = plugin.PLUGIN_SETTINGS.get("PLUGIN_FUNCS")
			# completely main sizer, holds absolutely everything
			scrollPanel = scrolled.ScrolledPanel(parent=self.mainPanel)
			scrollPanel.SetAutoLayout(1)
			scrollPanel.SetupScrolling(scroll_x=False)

			mainPluginSizer = wx.BoxSizer(wx.VERTICAL)
			# start plugin as an instance
			startButton = wx.Button(parent=scrollPanel, label="Start")
			startButton.Bind(wx.EVT_BUTTON, lambda event: self.startPluginInstance(plugin))
			mainPluginSizer.Add(startButton, 0, wx.EXPAND)
			# end plugin instance
			endButton = wx.Button(parent=scrollPanel, label="End")
			endButton.Bind(wx.EVT_BUTTON, lambda event: self.endPluginInstance())
			mainPluginSizer.Add(endButton, 0, wx.EXPAND)
			# a fold panel, looks pretty
			if pluginFuncs:
				for function in pluginFuncs:
					actualFunc = pluginFuncs[function]
					funcName = actualFunc.get("NAME") or function
					funcDescription = actualFunc.get("DESCRIPTION") or NO_DESCRIPTION_LABEL_TEXT

					# the actual panel to hold the elements
					contentPanel = wx.Panel(parent=scrollPanel)
					contentSizer = wx.BoxSizer(wx.VERTICAL)

					# the widgets parent
					widgetParent = contentPanel

					functionDescription = wx.StaticText(parent=widgetParent, label=funcDescription)
					contentSizer.Add(functionDescription)
					arguments = actualFunc.get("ARGUMENTS")  # returns None if there are no arguments
					argumentInputs = []
					if arguments:
						for argumentName in arguments:
							argument = arguments[argumentName]
							argumentName = argument.get("NAME") or argumentName
							argumentDescription = argument.get("DESCRIPTION") or NO_DESCRIPTION_LABEL_TEXT

							argumentBox = wx.StaticBoxSizer(orient=wx.VERTICAL, parent=contentPanel, label=argumentName)

							argumentDescription = wx.StaticText(
							 parent=argumentBox.GetStaticBox(), label=argumentDescription)
							argumentBox.Add(argumentDescription, 1, wx.ALIGN_CENTER | wx.EXPAND)
							argumentSelectionBody = self.processArgumentNotation(argument, argumentBox.GetStaticBox())
							argumentBox.Add(argumentSelectionBody, 1, wx.ALIGN_CENTER | wx.EXPAND)

							contentSizer.Add(argumentBox)

							# add the input element to the list
							argumentInputs.append([argumentName, argumentSelectionBody])
					runButton = wx.Button(
					 parent=widgetParent, label="Run Function")  # will add functionality later
					runButton.Bind(wx.EVT_BUTTON,
					               lambda event: self.runFunctionOfCurrentPlugin(function, argumentInputs))
					contentSizer.Add(runButton, 1, wx.ALIGN_CENTER | wx.EXPAND)
					contentPanel.SetSizer(contentSizer)
					# the important part that adds the widget panel to the foldopenbar
					mainPluginSizer.Add(contentPanel, 1, wx.ALIGN_CENTER | wx.EXPAND)
					# nothing else to do
			scrollPanel.SetSizer(mainPluginSizer)
			plugin.__ADDED_TO_GUI = False
			plugin.__PLUGIN_GUI = scrollPanel  # shouldn't be accesed by the plugin
			# the plugin will be added to the sizer by the `open` function

	def setTreeHierarchy(self, tree):
		hierarchy = {}
		root = tree.AddRoot("Plugins")
		for plugin in self.plugins:
			categoryName = plugin.PLUGIN_SETTINGS.get("CATEGORY")
			target = None

			# plugins without a name are not given a category
			if categoryName:
				# the category is created if it is not present
				if categoryName not in hierarchy:
					hierarchy[categoryName] = tree.AppendItem(root, categoryName)
					tree.SetItemData(hierarchy[categoryName], None)  # event.getdata() returns nothing
				target = hierarchy[categoryName]
			else:
				target = root

			pluginTreeItem = tree.AppendItem(target,
			                                 plugin.PLUGIN_SETTINGS.get("NAME") or plugin.B_V["FILE_NAME"])
			tree.SetItemData(pluginTreeItem, plugin)  # set the data returned by event.getdata()
		tree.Expand(root)

	def openPlugin(self, event):
		# set right panel to plugin form
		data = self.pluginTree.GetItemData(event.GetItem())
		if data:
			if not data.__ADDED_TO_GUI:
				self.pluginInfoSizer.Add(data.__PLUGIN_GUI, 1, wx.EXPAND)
				data.__ADDED_TO_GUI = True
			if self.lastPluginGui:
				self.pluginInfoSizer.Hide(self.lastPluginGui)
			self.lastPluginGui = data.__PLUGIN_GUI
			self.pluginInfoSizer.Show(data.__PLUGIN_GUI)
			self.refresh()

	def runFunctionOfCurrentPlugin(self, functionName, inputElements):
		# run the function with the specified arguments
		argumentsDict = {}
		for argument in inputElements:
			input = argument[1]  # will change
			argumentsDict[argument[0]] = input
		# apply dictionary as parameters
		getattr(self.currentPluginInstance, functionName)(**argumentsDict)

	def startPluginInstance(self, pluginToUse):
		# start the darn instance!
		self.currentPluginInstance = pluginToUse.Main()

	def endPluginInstance(self):
		# kill current instance if it exists
		if self.currentPluginInstance:
			del self.currentPluginInstance
			self.currentPluginInstance = None

	def processArgumentNotation(self, argument, parent):
		type = argument.get("TYPE")
		elementToReturn = None
		if type:
			type = type.split()  # split on space
			typeOfElement = type[0]
			typeArguments = type[1:]  # all elements other then the first
			if typeOfElement == "FILE":
				if len(typeArguments) == 0:
					elementToReturn = wx.FilePickerCtrl(parent=parent, message="Open file", style=wx.FD_OPEN)
				else:
					elementToReturn = wx.FilePickerCtrl(
					 parent=parent,
					 message="Open file",
					 wildcard=self.wildcardReturn(typeArguments),
					 style=wx.FD_OPEN)
			elif typeOfElement == "DROPDOWN":
				elementToReturn = wx.ComboBox(parent=parent, choices=typeArguments)
			elif typeOfElement == "SLIDER":
				minValue = None
				maxValue = None
				if len(typeArguments) == 0:
					minValue = 0
					maxValue = 100
				else:
					minValue = int(typeArguments[0])
					maxValue = int(typeArguments[1])
				elementToReturn = wx.Slider(
				 parent=parent, minValue=minValue, maxValue=maxValue, style=wx.SL_LABELS)
			elif typeOfElement == "TEXT":
				if len(typeArguments) == 0:
					elementToReturn = wx.TextCtrl(parent=parent, value="")
				else:
					elementToReturn = wx.TextCtrl(parent=parent, value=typeArguments[0].replace("_", " "))
		else:
			elementToReturn = wx.TextCtrl(parent=parent, value="")  # just a generic text box
		return elementToReturn

	def refresh(self):
		self.pluginInfoSizer.Layout()
		self.Layout()
		self.mainPanel.Layout()

	def wildcardReturn(self, fileTypes):
		wildcardList = []
		for file in fileTypes:
			fileParts = file.split("|")
			if len(fileParts) == 1:
				wildcardList.append("*" + fileParts[0])
			else:
				wildcardList.append(fileParts[1].replace("_", " ") + " (*" + fileParts[0] + ")")
				wildcardList.append("*" + fileParts[0])
		return "|".join(wildcardList)
