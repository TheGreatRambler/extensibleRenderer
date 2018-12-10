import sys
import os
import subprocess
import ctypes
import atexit

# comes from https://stackoverflow.com/a/19719292/9329945

process = None

def start(appType):
	if appType == "gui":
		pass
	else:
		# assume its command line
		global process
		process = subprocess.Popen(["python", getCorrectLocation("xrCommandLineInterface.py")] + sys.argv[1:])
		while process.poll() is None:
			# will block while the process is running
			pass

def getCorrectLocation(file):
	# concate this directory and the path to the file
	return os.path.realpath(os.path.join(os.path.dirname(__file__), file))

def stopProcess():
	# basically kill it
	process.terminate()

if __name__ == "__main__":
	atexit.register(stopProcess)
	if len(sys.argv) == 1:
		start("gui")
	else:
		# not needed, but why not be explicit
		start("text")
	sys.exit(0)

