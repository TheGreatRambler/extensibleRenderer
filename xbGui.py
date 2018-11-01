# pylint: disable=E1101

import wx
import wx.adv

import os
import os.path
import importlib

import plugins
import helpers.h
import xbGetPluginMenu

title = "eXtensible Backgrounds"


class TaskBarIcon(wx.adv.TaskBarIcon):
	def __init__(self, frame, icon):
		wx.adv.TaskBarIcon.__init__(self)
		self.frame = frame
		self.SetIcon(icon, title)
		self.Bind(wx.adv.EVT_TASKBAR_LEFT_DOWN, self.OnTaskBarLeftClick)

	def OnTaskBarActivate(self, evt):
		pass

	def OnTaskBarClose(self, evt):
		self.frame.Close()

	def OnTaskBarLeftClick(self, evt):
		self.frame.Show()
		self.frame.Restore()


class MainFrame(wx.Frame):
	def __init__(self, icon):
		wx.Frame.__init__(self, None, title=title, size=wx.Size(800, 600))

		self.appTaskBarIcon = TaskBarIcon(self, icon)  # mimimize to icon on taskbar
		self.SetIcon(icon)
		self.icon = icon

		self.mainSizer = wx.BoxSizer(wx.HORIZONTAL)
		#self.mainSizer.SetSizeHints(self)
		self.SetSizer(self.mainSizer)

		self.Bind(wx.EVT_ICONIZE, self.onMinimize)
		self.Bind(wx.EVT_CLOSE, self.onClose)

		self.Show(True)
		self.Center(wx.BOTH)

		self.allAccesiblePlugins = getPlugins()
		self.getPluginMenu()
		self.setupMenuBar()
		self.setupViewingPanel()

	def setupMenuBar(self):
		menuBar = wx.MenuBar()
		pluginMenu = wx.Menu()

		addPluginMenu = pluginMenu.Append(wx.ID_ANY, "Open Plugin Menu")
		self.Bind(wx.EVT_MENU, self.openSetMenuPlugin, source=addPluginMenu)

		closePluginMenu = pluginMenu.Append(wx.ID_ANY, "Close Plugin Menu")
		self.Bind(wx.EVT_MENU, self.closeSetMenuPlugin, source=closePluginMenu)

		menuBar.Append(pluginMenu, "Plugins")
		self.SetMenuBar(menuBar)

	def setupViewingPanel(self):
		self.viewingPanel = wx.Panel(parent=self, id=wx.ID_ANY)
		self.mainSizer.Add(self.viewingPanel, 1, wx.EXPAND, 0)

	def openSetMenuPlugin(self, event):
		self.mainSizer.Show(self.pluginSizer)
		self.mainSizer.Layout()

	def closeSetMenuPlugin(self, event):
		self.mainSizer.Hide(self.pluginSizer)
		self.mainSizer.Layout()

	def onClose(self, evt):
		self.appTaskBarIcon.RemoveIcon()
		self.appTaskBarIcon.Destroy()
		self.Destroy()

	def onMinimize(self, event):
		# minimize to tray
		if self.IsIconized():
			self.Hide()

	def getPluginMenu(self):
		self.pluginSizer = xbGetPluginMenu.getPluginMenu(plugins=self.allAccesiblePlugins, mainPanel=self)
		self.mainSizer.Add(self.pluginSizer, 1, wx.EXPAND, 0)
		self.mainSizer.Hide(self.pluginSizer)


class Main():
	def __init__(self):
		self.app = wx.App(False)
		self.mainFrame = MainFrame(
		 icon=wx.Icon(os.path.join(helpers.h.getScriptDir(), "resources", "icon.ico")))
		"""
		self.desktopEnvironment = helpers.h.getDesktopEnvironment()
		# test
		shaderInstance = plugins.renderShader.Main()
		shaderInstance.setShader(
		 shader=open("rainforest.glsl").read(), shaderType="shadertoy", vertexNum=50000)
		shaderInstance.setRenderMode("TRIANGLE_STRIP")
		shaderInstance.setResolution(1920, 1080)
		shaderInstance.setTime(0)
		helpers.h.setWallpaper(shaderInstance.render(), self.desktopEnvironment)
		"""
		self.app.MainLoop()


def getPlugins():
	thePlugins = []
	for plugin in dir(plugins):
		if plugin.startswith("Gp"):  # yes, its a graphics plugin!
			thisPlugin = importlib.import_module("plugins." + plugin)
			if not thisPlugin.PLUGIN_SETTINGS:
				thisPlugin.PLUGIN_SETTINGS = {}  # initalise to empty dict
			thisPlugin.B_V = {  # built in variables avalible at runtime
			 "FILE_NAME": os.path.basename(thisPlugin.__file__),
			 "FILE_DIR": os.path.dirname(thisPlugin.__file__),
			 "FILE_PATH": thisPlugin.__file__
			}
			thePlugins.append(thisPlugin)
	return thePlugins


Main()