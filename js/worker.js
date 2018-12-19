var instructionQueue = [];

var thisModule;
var thisModuleInstance;

var messageHandler = {
	"kill": function () {
		// nothing yet
	},
	"setPlugin": function (pluginPath) {
		if (thisModule && thisModuleInstance) {
			// call closing event handler on instance
			thisModuleInstance.onClose();
		}
		thisModule = require(pluginPath);
		thisModuleInstance = new thisModule.Main();
	}
}

process.on("message", function (message) {
	// handles all instructions
	// message.data can be undefined
	messageHandler[message.flag](message.data);
});