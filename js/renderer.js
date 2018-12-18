const cp = require("child_process");
const path = require("path");
const fs = require("fs");

var renderer = function () {
	this.results = [];
	this.verbose = false;
	this.startChild();
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
		this.sendMessage({
			flag: "setPlugin",
			data: filepath
		});
	} else {
		throw new Error("Plugin not supported");
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

p.startChild = function() {
	this.pluginChild = cp.fork(path.join(__dirname, "worker.js"), [], {
		stdio: ["ignore", "ignore", "ignore", "ipc"]
	});
	this.pluginChild.on("message", function(message) {
		if (message.flag = "returnedResult") {
			this.appendResult(message.content);
		}
	});
};

p.sendMessage = function(message) {
	this.pluginChild.send(message);
};

p.appendResult = function(result) {
	this.results.append(result);
};
