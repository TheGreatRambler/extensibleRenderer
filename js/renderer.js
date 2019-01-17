const cp = require("child_process");
const path = require("path");
const fs = require("fs");
const WebSocket = require("ws");
const getPort = require("get-port");
const ip = require("ip");
const canvas = require("canvas");

function start() {
	return new Promise(function(resolve, reject) {
		getPort().then(function(port) {
			var address = "ws://" + ip.address() + ":" + port;
			resolve(new renderer(port, address));
		});
	});
}

class renderer {
	constructor(port, wsAddress) {
		this.webSocketServer = new WebSocket.Server({
			port: port
		});
		this.webSocketServer.on("connection", function(ws) {
			ws.on("message", function(message) {
				// the only message is the rendering
				this.appendResult({
					flag: "render",
					data: message
				});
			});
		});
		this.address = wsAddress;
		this.results = [];
		this.verbose = false;
		// set default
		this.startChild();
		this.pluginSetResolution(1920, 1080);
	}

	setVerbose(verbose) {
		if (typeof verbose === "undefined") {
			// set verbose by default
			this.verbose = true;
		} else {
			this.verbose = verbose;
		}
	}

	pluginSetPlugin(name) {
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

	pluginSetResolution(width, height) {
		this.sendMessage({
			flag: "changeResolution",
			data: [width, height]
		})
	}

	pluginSetTime(time) {
		this.sendMessage({
			flag: "changeTime",
			data: time
		});
	}

	pluginSetValue(valueName, value) {
		this.sendMessage({
			flag: "setValue",
			data: [valueName, value]
		});
	}

	pluginRender() {
		this.sendMessage({
			flag: "render"
		});
	}

	pluginRenderInOrder(start, end, fps) {
		this.sendMessage({
			flag: "renderInOrder",
			data: [start, end, fps]
		});
	}

	isPlugin(pluginName) {
		allFiles = fs.readdirSync(path.join(__dirname, "plugins")).filter(function(element) {
			if (path.extname(element) === ".js") {
				return true;
			} else {
				return false;
			}
		}).map(function(element) {
			// removes ".js" from the filename
			return element.slice(0, -3);
		});
		// the plugin exists
		return allFiles.includes(pluginName);
	}

	startChild() {
		this.pluginChild = cp.fork(path.join(__dirname, "worker.js"), [], {
			stdio: ["ignore", "ignore", "ignore", "ipc"]
		});

		var messageHandler = {
			"returnedRender": function(data) {
				this.appendResult(data);
			}
		}

		this.pluginChild.on("message", function(message) {
			// data will be undefined, so the function doesnt break
			// if there is not any data
			messageHandler[message.flag](message.data);
		});
	}

	sendMessage(message) {
		this.pluginChild.send(message);
	}

	appendResult(result) {
		this.results.append(result);
	}

	testSpeed() {
		const theCanvas = canvas.createCanvas(1920, 1080);
		const ctx = theCanvas.getContext("2d");
		// From a local file path:
		const img = new canvas.Image();
		var self = this;
		img.onload = function() {
			ctx.drawImage(img, 0, 0);
			var imageData = ctx.getImageData(0, 0, theCanvas.width, theCanvas.height);
			console.log(imageData.data.length);
			self.webSocketServer.on("connection", function(connection) {
				connection.on("message", function(message) {
					console.timeEnd("message");
				});
			});

			const ws = new WebSocket(self.address);
			ws.on("open", function() {
				console.time("message");
				ws.send(imageData.data);
			});
		};
		img.onerror = err => {
			throw err
		}
		img.src = "test.jpg";
	}
}

start().then(function(instance) {
	instance.testSpeed()
});