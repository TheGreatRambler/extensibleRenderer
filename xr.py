import sys
import os
import subprocess
import ctypes
import atexit

# comes from https://stackoverflow.com/a/19719292/9329945

def start(appType):
	if appType == "gui":
		pass
	else:
		# assume its command line
		process = subprocess.Popen(["python", getCorrectLocation("xrCommandLineInterface.py")] + sys.argv[1:], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
		atexit.register(lambda: process.kill())
		process.wait()

def getCorrectLocation(file):
	# concate this directory and the path to the file
	return os.path.realpath(os.path.join(os.path.dirname(__file__), file))

if __name__ == "__main__":
	if len(sys.argv) == 1:
		# not needed, but why not be explicit
		start("text")
	else:
		start(sys.argv[1])
	sys.exit(0)

