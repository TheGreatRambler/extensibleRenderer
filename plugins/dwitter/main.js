const canvas = require("canvas");
const readline = require("readline");
const vm = require("vm");
const request = require("request");
const typedToBuffer = require("typedarray-to-buffer")
const http = require("http");
const lzFour = require("lz4js");
const findFreePort = require("find-free-port");
const ip = require("ip");


// canvas always the same size
const ctx = canvas.createCanvas(1920, 1080).getContext("2d");
// need to make background white and then reset fillstyle
ctx.fillStyle = "white";
ctx.fillRect(0, 0, ctx.canvas.width, ctx.canvas.height);
ctx.fillStyle = "black";

var currentMillisecondTime = 0;

var vmSandbox;
var vmScript;
var vmContext

var largeDataPort;

var currentDweetNum;

var serverAccessableData = {
	"dweetFile": undefined
};

var largeDataServer = http.createServer(function (request, response) {
	if (request.url === "/file") {
		var dataToSend = typedToBuffer(serverAccessableData["dweetFile"])
		response.writeHead(200, {
			"Content-type": "application/octet-stream",
			"Content-Length": dataToSend.byteLength
		});
		// send buffer with image data
		response.end(dataToSend);
	}
})


function setupCanvasCtx() {
	return new Promise(function (resolve, reject) {
		getDweetCode(currentDweetNum).then(function (code) {
			vmSandbox = {
				S: Math.sin,
				C: Math.cos,
				T: Math.tan,
				R: function (r, g, b, a) {
					// if no alpha, make it 1
					// round all colors
					var rgbaString = "rgba(" + (r | 0) + "," + (g | 0) + "," + (b | 0) + "," + (a || 1) + ")";
					return rgbaString;
				},
				c: ctx.canvas,
				x: ctx,
				t: 0
			};
			vmScript = new vm.Script(code);
			vmContext = vm.createContext(vmSandbox);
			resolve()
		});
	});
}

function getDweetCode(dweetNum) {
	return new Promise(function (resolve, reject) {
		request("https://www.dwitter.net/api/dweets/" + dweetNum + "/", function (error, response, body) {
			var code = JSON.parse(body).code;
			resolve(code);
		});
	});
}

function setup() {
	return new Promise(function (resolve, reject) {
		findFreePort(3000, function (err, freePort) {
			largeDataPort = freePort;
			// signal python script that we are started
			console.log("started");

			// instance to listen to command line
			const rl = readline.createInterface({
				input: process.stdin,
				output: process.stdout
			});

			rl.on("line", async function (line) {
				var data = line.split(" ")[1];
				switch (line.split(" ")[0]) {
					// choose based on command
					case "time":
						currentMillisecondTime = Number(data);
						break;
					case "render":
						renderAndPrint();
						break;
					case "address":
						returnAddress();
						break;
					case "setDweet":
						currentDweetNum = Number(data);
						await setupCanvasCtx();
						break;
				}
				console.log("next");
			});
			// start server
			largeDataServer.listen(largeDataPort);
		});
	});
}

function renderAndPrint() {
	vmContext.t = currentMillisecondTime / 1000; // number of seconds as a float
	vmScript.runInContext(vmContext);
	var imageData = ctx.getImageData(0, 0, 1920, 1080).data;
	// will keep alpha even though it is not needed
	/*
	var realImageData = new Uint8Array((imageData.length * (3 / 4)) | 0); // should be an int because of rounding
	var index = 0;
	for (var i = 0; i < imageData.length; i++) {
		if (i % 4 === 0) {
			realImageData[index] = imageData[i];
			index++;
		}
	}
	*/
	var compressedData = lzFour.compress(imageData);
	serverAccessableData["dweetFile"] = compressedData
	// signal python that the data is on the server
	// implied by next
	//console.log("done");
}

function returnAddress() {
	console.log("D" + "http://" + ip.address() + ":" + largeDataPort);
}

setup();

process.on("SIGTERM", function () {
	// can do stuff
	process.exit(0);
});