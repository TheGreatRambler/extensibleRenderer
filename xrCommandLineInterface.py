import click

import yaml
import json
import signal
import sys
import os

import xbRenderingProcess as xb

# TODO make this command line program loads better please!

# the message to be displayed when seeing the version
VERSION_MESSAGE = None
VERSION = "0.0.1"

MAIN_FILENAME = "python xr.py"

def setVersionGraphic():
	VERSION_GRAPHIC = None
	with open("version_string.txt", "r", encoding="utf8") as versionString:
		VERSION_GRAPHIC = versionString.read()
	COPYRIGHT = "Copyright TheGreatRambler, MIT License, All rights reserved"
	global VERSION_MESSAGE
	VERSION_MESSAGE = VERSION_GRAPHIC + "\n" + VERSION + " " + COPYRIGHT
setVersionGraphic()

def getNumCores():
	cpu_count = None
	if hasattr(os, "sched_getaffinity"):
		# https://stackoverflow.com/a/25636145/9329945
		cpu_count = len(os.sched_getaffinity(0))
	else:
		cpu_count = os.cpu_count()
	# if still none, make default value
	if cpu_count is None:
		# sensible default
		cpu_count = 4
	return cpu_count
	
	

@click.group()
@click.version_option(version=VERSION, message=VERSION_MESSAGE)
def cli():
	pass

@cli.command()
@click.option("-i", "--input-plugin", "inputPlugin", type=click.STRING, required=True)
@click.option("-p", "--processes", "processes", type=int, required=False, default=getNumCores())
@click.option("-f", "--fps", "fps", type=int, required=False, default=60) # not a shabby speed
@click.option("-m", "--milliseconds", "millisecondRanges", type=click.STRING, required=True)
def render(inputPlugin, processes, fps, millisecondRanges):
	# pylint complains about the argument number
	# TODO stuck when creating this instance for dwitter
	instance = xb.createMultiCoreInterface(processes, json.loads(millisecondRanges), inputPlugin, fps) #pylint: disable=E1121
	print(len(instance.start().waitForEnd()))

@cli.command()
@click.option("-i", "--input-plugin", "inputPlugin", type=click.STRING, required=True)
@click.option("-j", "--json", "notPretty", required=False, is_flag=True, default=False)
def info(inputPlugin, notPretty):
	# print info about plugins and exit
	# print info for each plugin and be done
	# creates a quick instance
	instance = xb.renderInterface()
	# don't create instance
	instance.pluginSetPlugin(inputPlugin, False).getPluginInfo()
	allResults = instance.stop()
	# prints the last element in the return array, which is the PLUGIN_SETTINGS dict
	# yaml makes pretty printing, only reason
	if notPretty is not True:
		click.echo("\n" + yaml.dump(allResults[-1], indent=4, default_flow_style=False))
	else:
		click.echo(json.dumps(allResults[-1], indent=4))


def setupClickFunctions():
	cli(prog_name=MAIN_FILENAME)

def signal_handler(signal, frame):
	sys.exit(0)

if __name__ == "__main__":
	signal.signal(signal.SIGINT, signal_handler)
	setupClickFunctions()
