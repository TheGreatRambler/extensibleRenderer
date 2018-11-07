# pylint: disable=E1101

import wx
import wx.lib.agw.foldpanelbar as fpb

import helpers.h

NO_DESCRIPTION_LABEL_TEXT = ""


class getPluginMenu(wx.BoxSizer):
	def __init__(self, plugins, mainPanel):

		self.mainPanel = mainPanel

		wx.BoxSizer.__init__(self, orient=wx.VERTICAL)
		self.plugins = plugins
		self.lastPluginGui = None

		#self.Bind(wx.EVT_ICONIZE, self.onMinimize)
		#self.Bind(wx.EVT_CLOSE, self.onClose)

		self.pluginSizer = self.getPluginChoiceSizer(parent=mainPanel)
		self.pluginInfoSizer = self.getPluginInfoSizer(parent=mainPanel)

		self.Add(self.pluginSizer, 0, wx.EXPAND)
		self.Add(self.pluginInfoSizer)

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
			# a fold panel, looks pretty
			pluginFoldOpenPanel = fpb.FoldPanelBar(parent=self.mainPanel, agwStyle=fpb.FPB_VERTICAL)
			if pluginFuncs:
				for function in pluginFuncs:
					actualFunc = pluginFuncs[function]
					funcName = actualFunc.get("NAME") or function
					funcDescription = actualFunc.get("DESCRIPTION") or NO_DESCRIPTION_LABEL_TEXT

					# the panel to hold the function
					funcPanel = pluginFoldOpenPanel.AddFoldPanel(caption=funcName, collapsed=True)
					# TODO add elements to this panel, not to the sizer

					# the sizer to add the elements, will be added to panel
					functionSizer = wx.BoxSizer(wx.VERTICAL)

					functionDescription = wx.StaticText(parent=funcPanel, label=funcDescription)
					functionSizer.Add(functionDescription)
					arguments = actualFunc.get("ARGUMENTS")  # returns None if there are no arguments
					if arguments:
						for argumentName in arguments:
							argument = arguments[argumentName]
							argumentName = argument.get("NAME") or argumentName
							argumentDescription = argument.get("DESCRIPTION") or NO_DESCRIPTION_LABEL_TEXT
							argumentName = wx.StaticText(parent=funcPanel, label=argumentName)
							functionSizer.Add(argumentName)
							argumentDescription = wx.StaticText(parent=funcPanel, label=argumentDescription)
							functionSizer.Add(argumentDescription)
							argumentSelectionBody = self.processArgumentNotation(argument, funcPanel)
							functionSizer.Add(argumentSelectionBody)
					runButton = wx.Button(parent=funcPanel, label="Run Function")  # will add functionality later
					functionSizer.Add(runButton)
					# way to add the sizer to the foldable panel, somewhat verbose
					# the element inside will expand to fill it
					pluginFoldOpenPanel.AddFoldPanelWindow(panel=funcPanel, window=funcPanel, flags=fpb.FPB_ALIGN_WIDTH)
			plugin.__ADDED_TO_GUI = False
			plugin.__PLUGIN_GUI = pluginFoldOpenPanel  # shouldn't be accesed by the plugin
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
				self.pluginInfoSizer.Add(data.__PLUGIN_GUI)
				data.__ADDED_TO_GUI = True
			if self.lastPluginGui:
				self.pluginInfoSizer.Hide(self.lastPluginGui)
			self.lastPluginGui = data.__PLUGIN_GUI
			self.pluginInfoSizer.Show(data.__PLUGIN_GUI)
			self.refresh()

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
