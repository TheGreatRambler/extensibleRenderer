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
		// remove ".js" on end
		thisModule = require(pluginPath.slice(0, -3));
		thisModuleInstance = new thisModule.Main();
	}
}

process.on("message", function (message) {
	// handles all instructions
	// message.data can be undefined
	messageHandler[message.flag](message.data);
});
