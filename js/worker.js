const ws = require("ws");

var instructionQueue = [];

var thisModule;
var thisModuleInstance;

var thisWebsocketInstance;

var websocketReady = false;

var wsNotReadyRenderBuffer = [];

var messageHandler = {
	"kill": function() {
		// nothing yet
	},
	"setPlugin": function(pluginPath) {
		if (thisModule && thisModuleInstance) {
			// call closing event handler on instance
			thisModuleInstance.onClose();
		}
		// remove ".js" on end
		thisModule = require(pluginPath.slice(0, -3));
		thisModuleInstance = new thisModule.Main();
	},
	"wsAddress": function(address) {
		var thisWebsocketInstance = new ws(address);
		thisWebsocketInstance.on("open", function() {
			websocketReady = true;
		});
	}
}

function sendRender(render, time) {
	if (websocketReady) {
		if (wsNotReadyRenderBuffer) {
			wsNotReadyRenderBuffer.forEach(function(element) {
				thisWebsocketInstance.send(element.render);
			});
			// delete the buffer
			wsNotReadyRenderBuffer = undefined;
		} else {
			thisWebsocketInstance.send(render);
		}
	} else {
		wsNotReadyRenderBuffer.append({
			time: time,
			render: render
		});
	}
}

process.on("message", function(message) {
	// handles all instructions
	// message.data can be undefined
	messageHandler[message.flag](message.data);
});