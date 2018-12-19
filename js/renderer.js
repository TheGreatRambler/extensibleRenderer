const cp = require("child_process");
const path = require("path");
const fs = require("fs");

var renderer = function() {
    this.results = [];
    this.verbose = false;
    // set default
    this.pluginSetResolution(1920, 1080);
    this.startChild();
}

var p = renderer.prototype;

p.setVerbose = function(verbose) {
    if (typeof verbose === "undefined") {
        // set verbose by default
        this.verbose = true;
    } else {
        this.verbose = verbose;
    }
}

p.pluginSetPlugin = function(name) {
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

p.pluginSetResolution = function(width, height) {
    this.renderMemory = undefined; // need to have a working shm implementation on windows
    this.sendMessage({
        flag: "changeResolution",
        data: [width, height]
    })
};

p.pluginSetTime = function(time) {
    this.sendMessage({
        flag: "changeTime",
        data: time
    });
};

p.pluginSetValue = function(valueName, value) {
    this.sendMessage({
        flag: "setValue",
        data: [valueName, value]
    });
};

p.pluginRender = function() {
    this.sendMessage({
        flag: "render"
    });
};

p.pluginRenderInOrder = function(start, end, fps) {
    this.sendMessage({
        flag: "renderInOrder",
        data: [start, end, fps]
    });
};

p.isPlugin = function(pluginName) {
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
};

p.startChild = function() {
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
};

p.sendMessage = function(message) {
    this.pluginChild.send(message);
};

p.appendResult = function(result) {
    this.results.append(result);
};