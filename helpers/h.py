# pylint: disable=E1101

import platform
import tempfile
import os
import sys
import inspect
import subprocess
import re
import configparser
import codecs
import helpers.h
import wx


def is_running(process):
	#From http://www.bloggerpolis.com/2011/05/how-to-check-if-a-process-is-running-using-python/
	# and http://richarddingwall.name/2009/06/18/windows-equivalents-of-ps-and-kill-commands/
	try:  #Linux/Unix
		s = subprocess.Popen(["ps", "axw"], stdout=subprocess.PIPE)
	except:  #Windows
		s = subprocess.Popen(["tasklist", "/v"], stdout=subprocess.PIPE)
	for x in s.stdout:
		if re.search(process, x):
			return True
	return False


def get_config_dir(app_name):
	if "XDG_CONFIG_HOME" in os.environ:
		confighome = os.environ['XDG_CONFIG_HOME']
	elif "APPDATA" in os.environ:  # On Windows
		confighome = os.environ['APPDATA']
	else:
		try:
			from xdg import BaseDirectory
			confighome = BaseDirectory.xdg_config_home
		except ImportError:  # Most likely a Linux/Unix system anyway
			confighome = os.path.join(get_home_dir(), ".config")
	configdir = os.path.join(confighome, app_name)
	return configdir


def get_home_dir():
	if sys.platform == "cygwin":
		home_dir = os.getenv('HOME')
	else:
		home_dir = os.getenv('USERPROFILE') or os.getenv('HOME')
	if home_dir is not None:
		return os.path.normpath(home_dir)
	else:
		raise KeyError("Neither USERPROFILE or HOME environment variables set.")


def getDesktopEnvironment():
	#From http://stackoverflow.com/questions/2035657/what-is-my-current-desktop-environment
	# and http://ubuntuforums.org/showthread.php?t=652320
	# and http://ubuntuforums.org/showthread.php?t=652320
	# and http://ubuntuforums.org/showthread.php?t=1139057
	if sys.platform in ["win32", "cygwin"]:
		return "windows"
	elif sys.platform == "darwin":
		return "mac"
	else:  #Most likely either a POSIX system or something not much common
		desktop_session = os.environ.get("DESKTOP_SESSION")
		if desktop_session is not None:  #easier to match if we doesn't have  to deal with caracter cases
			desktop_session = desktop_session.lower()
			if desktop_session in [
			  "gnome", "unity", "cinnamon", "mate", "xfce4", "lxde", "fluxbox", "blackbox", "openbox",
			  "icewm", "jwm", "afterstep", "trinity", "kde"
			]:
				return desktop_session
			## Special cases ##
			# Canonical sets $DESKTOP_SESSION to Lubuntu rather than LXDE if using LXDE.
			# There is no guarantee that they will not do the same with the other desktop environments.
			elif "xfce" in desktop_session or desktop_session.startswith("xubuntu"):
				return "xfce4"
			elif desktop_session.startswith("ubuntu"):
				return "unity"
			elif desktop_session.startswith("lubuntu"):
				return "lxde"
			elif desktop_session.startswith("kubuntu"):
				return "kde"
			elif desktop_session.startswith("razor"):  # e.g. razorkwin
				return "razor-qt"
			elif desktop_session.startswith("wmaker"):  # e.g. wmaker-common
				return "windowmaker"
		if os.environ.get('KDE_FULL_SESSION') == 'true':
			return "kde"
		elif os.environ.get('GNOME_DESKTOP_SESSION_ID'):
			if not "deprecated" in os.environ.get('GNOME_DESKTOP_SESSION_ID'):
				return "gnome2"
		#From http://ubuntuforums.org/showthread.php?t=652320
		elif is_running("xfce-mcs-manage"):
			return "xfce4"
		elif is_running("ksmserver"):
			return "kde"
		return "unknown"


def setWallpaper(image, desktop_env):
	# Note: There are two common Linux desktop environments where
	# I have not been able to set the desktop background from
	# command line: KDE, Enlightenment
	file_loc = None
	if desktop_env == "windows":
		file_loc = os.path.join(helpers.h.getScriptDir(), "current-background.bmp")
	else:
		file_loc = os.path.join(helpers.h.getScriptDir(), "current-background.png")
	image.save(file_loc)

	try:
		if desktop_env in ["gnome", "unity", "cinnamon"]:
			uri = "'file://%s'" % file_loc
			args = ["gsettings", "set", "org.gnome.desktop.background", "picture-uri", uri]
			subprocess.Popen(args)
		elif desktop_env == "mate":
			try:  # MATE >= 1.6
				# info from http://wiki.mate-desktop.org/docs:gsettings
				args = ["gsettings", "set", "org.mate.background", "picture-filename", "'%s'" % file_loc]
				subprocess.Popen(args)
			except:  # MATE < 1.6
				# From https://bugs.launchpad.net/variety/+bug/1033918
				args = [
				 "mateconftool-2", "-t", "string", "--set", "/desktop/mate/background/picture_filename",
				 '"%s"' % file_loc
				]
				subprocess.Popen(args)
		elif desktop_env == "gnome2":  # Not tested
			# From https://bugs.launchpad.net/variety/+bug/1033918
			args = [
			 "gconftool-2", "-t", "string", "--set", "/desktop/gnome/background/picture_filename",
			 '"%s"' % file_loc
			]
			subprocess.Popen(args)
		## KDE4 is difficult
		## see http://blog.zx2c4.com/699 for a solution that might work
		elif desktop_env in ["kde3", "trinity"]:
			# From http://ubuntuforums.org/archive/index.php/t-803417.html
			args = 'dcop kdesktop KBackgroundIface setWallpaper 0 "%s" 6' % file_loc
			subprocess.Popen(args, shell=True)
		elif desktop_env == "xfce4":
			#From http://www.commandlinefu.com/commands/view/2055/change-wallpaper-for-xfce4-4.6.0
			args0 = [
			 "xfconf-query", "-c", "xfce4-desktop", "-p", "/backdrop/screen0/monitor0/image-path", "-s",
			 file_loc
			]
			args1 = [
			 "xfconf-query", "-c", "xfce4-desktop", "-p", "/backdrop/screen0/monitor0/image-style", "-s", "3"
			]
			args2 = [
			 "xfconf-query", "-c", "xfce4-desktop", "-p", "/backdrop/screen0/monitor0/image-show", "-s",
			 "true"
			]
			subprocess.Popen(args0)
			subprocess.Popen(args1)
			subprocess.Popen(args2)
			args = ["xfdesktop", "--reload"]
			subprocess.Popen(args)
		elif desktop_env == "razor-qt":  #TODO: implement reload of desktop when possible
			desktop_conf = configparser.ConfigParser()
			# Development version
			desktop_conf_file = os.path.join(get_config_dir("razor"), "desktop.conf")
			if os.path.isfile(desktop_conf_file):
				config_option = r"screens\1\desktops\1\wallpaper"
			else:
				desktop_conf_file = os.path.join(get_home_dir(), ".razor/desktop.conf")
				config_option = r"desktops\1\wallpaper"
			desktop_conf.read(os.path.join(desktop_conf_file))
			try:
				if desktop_conf.has_option("razor", config_option):  #only replacing a value
					desktop_conf.set("razor", config_option, file_loc)
					with codecs.open(desktop_conf_file, "w", encoding="utf-8", errors="replace") as f:
						desktop_conf.write(f)
			except:
				pass
		elif desktop_env in ["fluxbox", "jwm", "openbox", "afterstep"]:
			#http://fluxbox-wiki.org/index.php/Howto_set_the_background
			# used fbsetbg on jwm too since I am too lazy to edit the XML configuration
			# now where fbsetbg does the job excellent anyway.
			# and I have not figured out how else it can be set on Openbox and AfterSTep
			# but fbsetbg works excellent here too.
			try:
				args = ["fbsetbg", file_loc]
				subprocess.Popen(args)
			except:
				sys.stderr.write("ERROR: Failed to set wallpaper with fbsetbg!\n")
				sys.stderr.write("Please make sre that You have fbsetbg installed.\n")
		elif desktop_env == "icewm":
			# command found at http://urukrama.wordpress.com/2007/12/05/desktop-backgrounds-in-window-managers/
			args = ["icewmbg", file_loc]
			subprocess.Popen(args)
		elif desktop_env == "blackbox":
			# command found at http://blackboxwm.sourceforge.net/BlackboxDocumentation/BlackboxBackground
			args = ["bsetbg", "-full", file_loc]
			subprocess.Popen(args)
		elif desktop_env == "lxde":
			args = "pcmanfm --set-wallpaper %s --wallpaper-mode=scaled" % file_loc
			subprocess.Popen(args, shell=True)
		elif desktop_env == "windowmaker":
			# From http://www.commandlinefu.com/commands/view/3857/set-wallpaper-on-windowmaker-in-one-line
			args = "wmsetbg -s -u %s" % file_loc
			subprocess.Popen(args, shell=True)
		#elif desktop_env=="enlightenment": # I have not been able to make it work on e17. On e16 it would have been something in this direction
		#    args = "enlightenment_remote -desktop-bg-add 0 0 0 0 %s" % file_loc
		#    subprocess.Popen(args,shell=True)
		elif desktop_env == "windows":  #Not tested since I do not run this on Windows
			import ctypes
			SPI_SETDESKWALLPAPER = 20
			ctypes.windll.user32.SystemParametersInfoW(SPI_SETDESKWALLPAPER, 0, file_loc, 0)
		elif desktop_env == "mac":  #Not tested since I do not have a mac
			#From https://stackoverflow.com/questions/431205/how-can-i-programatically-change-the-background-in-mac-os-x
			try:
				from appscript import app, mactypes
				app('Finder').desktop_picture.set(mactypes.File(file_loc))
			except ImportError:
				#import subprocess
				SCRIPT = """/usr/bin/osascript<<END
				tell application "Finder" to
				set desktop picture to POSIX file "%s"
				end tell
				END"""
				subprocess.Popen(SCRIPT % file_loc, shell=True)
		else:
			# error
			pass
		return True
	except:
		# error
		return False


def getScriptDir():
	if getattr(sys, 'frozen', False):  # py2exe, PyInstaller, cx_Freeze
		path = os.path.abspath(sys.executable)
	else:
		path = inspect.getframeinfo(sys._getframe(1)).filename
	path = os.path.realpath(path)
	return os.path.dirname(path)


def centerInPanel(element, panel):
	centerSizer = wx.BoxSizer(wx.VERTICAL)
	centerSizer.AddStretchSpacer()
	centerSizer.Add(element, 0, wx.CENTER)
	centerSizer.AddStretchSpacer()
	panel.SetSizer(centerSizer)


def fillEntirePanel(element, panel, padding=1):
	sizer = wx.BoxSizer(wx.VERTICAL)
	sizer.Add(element, 1, wx.EXPAND | wx.ALL, padding)
	panel.SetSizer(sizer)

def getValueOfControl(wxControl):
	classType = type(wxControl)
	valueToReturn = None
	if classType == wx.FilePickerCtrl:
		valueToReturn = open(wxControl.GetPath(), "r")
	elif classType == wx.ComboBox:
		# get the value of the selected dropdown value
		valueToReturn = wxControl.GetString(wxControl.GetSelection())
	elif classType == wx.Slider:
		valueToReturn = wxControl.GetValue()
	elif classType == wx.TextCtrl:
		# get text of first line (only line in this case)
		valueToReturn = wxControl.GetLineText(0)
	elif classType == wx.ColourPickerCtrl:
		# return as rgb tuple
		valueToReturn = wxControl.GetColour().Get(includeAlpha=False)
	return valueToReturn

class onWriteMemoryFile():
	# a simple class that creates a "file object" that calls a callback when lines are written
	def __init__(self, callback):
		self.callback = callback
		self.currentBytesArray = bytearray()
	def write(self, s):
		if len(s) != 0:
			self.currentBytesArray.extend(s)
			# if the buffer ends a line
			if (self.currentBytesArray.decode()[-1] == "\n"):
				self.callback(self.currentBytesArray[:-1].decode(encoding="utf-8"))
				self.currentBytesArray = bytearray() # clear
	def flush(self):
		# not needed
		pass
