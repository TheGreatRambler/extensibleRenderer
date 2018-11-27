import click

import xbRenderingProcess

# TODO make this command line program loads better please!

VERSION = "0.0.1"

@click.group()
def cli():
    pass

@cli.command()
@cli.option("-i", "--input-plugin", type=click.STRING, required=True)
@cli.option("-o", "--output-plugin", type=click.STRING, required=True)
def render(i, o):
	pass

@cli.command()
@cli.option("-i", "--input-plugin", type=click.STRING, required=False)
@cli.option("-o", "--output-plugin", type=click.STRING, required=False)
def info(i, o):
	# print info about plugins and exit
	pass

def setupClickFunctions():
	click.version_option(VERSION)
	cli()

if __name__ == "__main__":
	setupClickFunctions()