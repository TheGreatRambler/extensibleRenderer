const program = require("commander");
const Worker = require("tiny-worker");

versionString = "1.0.0";

program
	.version(versionString)
	.option("-r, --render", "Render frames (or a frame)")
	.option("-I, --info", "Show info (overrides --render)")
	.option("-i, --input-plugin", "Specify the rendering plugin name or absolute path")
	.parse(process.argv);

// stuff here