const cp = require("child_process");
const path = require("path");
const fs = require("fs");

var renderer = function () {
	this.results = [];
	this.verbose = false;
}

var p = renderer.prototype;

p.setVerbose = function (verbose) {
	if (typeof verbose === "undefined") {
		// set verbose by default
		this.verbose = true;
	} else {
		this.verbose = verbose;
	}
}

p.setPlugin = function (name) {
	var filePath;
	if (path.isAbsolute(name)) {
		// use the exact file to start the instance
		filePath = name;
	} else {
		if (this.isPlugin(name)) {
			filePath = path.join(__dirname, "plugins", name + ".js");
		} else {
			// it failed
			filePath = false;
		}
	}
	if (filePath) {
		this.pluginProcess = cp.fork(filePath);
	}
}

p.isPlugin = function (pluginName) {
	allFiles = fs.readdirSync(path.join(__dirname, "plugins")).filter(function (element) {
		if (path.extname(element) === ".js") {
			return true;
		} else {
			return false;
		}
	}).map(function (element) {
		// removes ".js" from the filename
		return element.slice(0, -3);
	});
	// the plugin exists
	return allFiles.includes(pluginName);
};