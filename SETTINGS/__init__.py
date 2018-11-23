# pylint: disable=E1101

import wx
from dotmap import DotMap

# the file that has all application settings
# color theme
theme = DotMap({
	"set_button": wx.Colour(134, 168, 185),
	"plugin_variable_background": wx.Colour(168, 165, 18)
})

render = DotMap({
	"default_resolution": (800, 600)
})