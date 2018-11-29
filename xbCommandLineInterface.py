import click

import yaml
import signal
import sys

import xbRenderingProcess as xb

# TODO make this command line program loads better please!

# the message to be displayed when seeing the version
VERSION_MESSAGE = None
VERSION = "0.0.1"

def setVersionGraphic():
	VERSION_GRAPHIC = None
	with open("version_string.txt", "r", encoding="utf8") as versionString:
		VERSION_GRAPHIC = versionString.read()
	COPYRIGHT = "Copyright TheGreatRambler, MIT License, All rights reserved"
	global VERSION_MESSAGE
	VERSION_MESSAGE = VERSION_GRAPHIC + "\n" + VERSION + " " + COPYRIGHT
setVersionGraphic()

@click.group()
@click.version_option(version=VERSION, message=VERSION_MESSAGE)
def cli():
	pass

@cli.command()
@click.option("-i", "--input-plugin", "i", type=click.STRING, required=True)
@click.option("-o", "--output-plugin", "o", type=click.STRING, required=True)
def render(i, o):
	pass

@cli.command()
@click.option("-i", "--input-plugin", "i", type=click.STRING, required=False)
@click.option("-o", "--output-plugin", "o", type=click.STRING, required=False)
def info(i, o):
	# print info about plugins and exit
	# print info for each plugin and be done
	# creates a quick instance
	instance = xb.renderInterface()
	if i is not None:
		# don't create instance
		instance.pluginSetPlugin(i, False)
		instance.getPluginInfo()
		allResults = instance.stop()
		# prints the last element in the return array, which is the PLUGIN_SETTINGS dict
		# yaml makes pretty printing, only reason
		print("\n" + yaml.dump(allResults[-1], indent=4, default_flow_style=False))
	# o not yet supported


def setupClickFunctions():
	cli()

def signal_handler(signal, frame):
	sys.exit(0)

if __name__ == "__main__":
	signal.signal(signal.SIGINT, signal_handler)
	setupClickFunctions()