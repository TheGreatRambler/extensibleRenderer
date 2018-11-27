import click

import xbRenderingProcess

# TODO make this command line program loads better please!

VERSION = "0.0.1"

@click.command()
@click.option("-i", "--input-plugin", type=click.STRING, required=True)
@click.option("-o", "--output-plugin", type=click.STRING, required=True)
def render(i, o):
	pass

@click.command()
@click.option("-i", "--input-plugin", type=click.STRING, required=False)
@click.option("-o", "--output-plugin", type=click.STRING, required=False)
def info(i, o):
	# print info about plugins and exit
	pass

def setupClickFunctions():
	click.version_option(VERSION)

if __name__ == "__main__":
	setupClickFunctions()