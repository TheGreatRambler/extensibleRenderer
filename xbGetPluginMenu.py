# pylint: disable=E1101

import wx
import wx.lib.scrolledpanel as Scroller

import helpers.h

NO_DESCRIPTION_LABEL_TEXT = ""


class getPluginMenu(wx.BoxSizer):
	def __init__(self, plugins, mainPanel):

		wx.BoxSizer.__init__(self, orient=wx.VERTICAL)
		self.plugins = plugins
		self.lastPluginGui = None

		#self.Bind(wx.EVT_ICONIZE, self.onMinimize)
		#self.Bind(wx.EVT_CLOSE, self.onClose)

		self.PluginPanel = self.getLeftSide(parent=mainPanel)
		self.FunctionPanel = self.getRightSide(parent=mainPanel)

		self.Add(self.PluginPanel)
		self.Add(self.FunctionPanel)

		self.createPluginForms()  # create the forms so they can be opened

	def getLeftSide(self, parent):
		pluginPanel = wx.Panel(parent=parent, id=wx.ID_ANY)

		self.pluginTree = wx.TreeCtrl(parent=pluginPanel, id=wx.ID_ANY, style=wx.TR_HAS_BUTTONS)
		self.setTreeHierarchy(tree=self.pluginTree)

		self.pluginTree.Bind(wx.EVT_TREE_SEL_CHANGED, self.openPlugin)

		helpers.h.fillEntirePanel(element=self.pluginTree, panel=pluginPanel, padding=8)

		return pluginPanel

	def getRightSide(self, parent):
		FunctionPanel = Scroller.ScrolledPanel(parent=parent, id=wx.ID_ANY)
		self.FunctionPanelSizer = wx.BoxSizer(wx.VERTICAL)
		FunctionPanel.SetSizer(self.FunctionPanelSizer)
		#for now, nothing
		return FunctionPanel

	def createPluginForms(self):
		for plugin in self.plugins:
			pluginFuncs = plugin.PLUGIN_SETTINGS.get("PLUGIN_FUNCS")
			pluginSizer = wx.BoxSizer(wx.VERTICAL)
			if pluginFuncs:
				for function in pluginFuncs:
					actualFunc = pluginFuncs[function]
					# name is misleading, but it encompasses the entire function
					functionArgumentsBox = wx.StaticBoxSizer(
					 orient=wx.VERTICAL, parent=self.FunctionPanel, label=actualFunc.get("NAME") or function)
					functionDescription = wx.StaticText(
					 parent=self.FunctionPanel, label=actualFunc.get("DESCRIPTION") or NO_DESCRIPTION_LABEL_TEXT)
					functionArgumentsBox.Add(functionDescription)
					arguments = actualFunc.get("ARGUMENTS")  # returns None if there are no arguments
					if arguments:
						for argumentName in arguments:
							argument = arguments[argumentName]
							argumentName = wx.StaticText(
							 parent=self.FunctionPanel, label=argument.get("NAME") or argumentName)
							functionArgumentsBox.Add(argumentName)
							argumentDescription = wx.StaticText(
							 parent=self.FunctionPanel, label=argument.get("DESCRIPTION") or NO_DESCRIPTION_LABEL_TEXT)
							functionArgumentsBox.Add(argumentDescription)
							argumentSelectionBody = self.processArgumentNotation(argument, self.FunctionPanel)
							functionArgumentsBox.Add(argumentSelectionBody)
					runButton = wx.Button(
					 parent=self.FunctionPanel, label="Run Function")  # will add functionality later
					functionArgumentsBox.Add(runButton)
					pluginSizer.Add(functionArgumentsBox)  # add to main boxsizer
			plugin.__PLUGIN_GUI = pluginSizer  # shouldn't be accesed by the plugin

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
			if self.lastPluginGui:
				self.FunctionPanelSizer.Hide(self.lastPluginGui)
				self.FunctionPanelSizer.Detach(self.lastPluginGui)
				self.FunctionPanelSizer.Layout()
			self.lastPluginGui = data.__PLUGIN_GUI
			self.FunctionPanelSizer.Add(data.__PLUGIN_GUI)
			self.FunctionPanel.SetupScrolling()

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
