import click

import xbRenderingProcess

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
@click.option("-i", "--input-plugin", type=click.STRING, required=True)
@click.option("-o", "--output-plugin", type=click.STRING, required=True)
def render(i, o):
	pass

@cli.command()
@click.option("-i", "--input-plugin", type=click.STRING, required=False)
@click.option("-o", "--output-plugin", type=click.STRING, required=False)
def info(i, o):
	# print info about plugins and exit
	pass

def setupClickFunctions():
	cli()

if __name__ == "__main__":
	setupClickFunctions()