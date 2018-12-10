const canvas = require("canvas");
const readline = require("readline");
const vm = require("vm");
const request = require("request");
const typedToBuffer = require("typedarray-to-buffer")
const http = require("http");
const lzFour = require("lz4js");
const findFreePort = require("find-free-port");
const ip = require("ip");

// default canvas size, but it can be different
var width = 1920;
var height = 1080;

// make the canvas massive so it can acommodate everything
const ctx = canvas.createCanvas(10000, 10000).getContext("2d");

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
				t: 0,
				u: new Function(code) // some dweets use their own code
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
				var data = line.split(" ");
				switch (line.split(" ")[0]) {
					// choose based on command
					case "render":
						// render with millisecond range
						renderAndPrint(Number(data[1]), Number(data[2]), Number(data[3]));
						break;
					case "address":
						returnAddress();
						break;
					case "setDweet":
						currentDweetNum = Number(data[1]);
						await setupCanvasCtx();
						break;
					case "setSize":
						width = Number(data[1]);
						height = Number(data[2]);
						break;
				}
				console.log("next");
			});
			// start server
			largeDataServer.listen(largeDataPort);
		});
	});
}

function concateTypedArrays(type, arrays) {
	// http://2ality.com/2015/10/concatenating-typed-arrays.html
	var totalLength = 0;
	for (var i = 0; i < arrays.length; i++) {
		totalLength += arrays[i].length;
	}
	var result = new type(totalLength);
	var offset = 0;
	for (var i = 0; i < arrays.length; i++) {
		console.log(offset)
		result.set(arrays[i], offset);
		offset += arrays[i].length;
	}
	return result;
}

function renderAndPrint(start, end, offset) {
	var allRenderings = []
	for (var millisecond = start; millisecond <= end;) {
		vmContext.t = millisecond / 1000; // number of seconds as a float
		vmScript.runInContext(vmContext);
		// add the image to the renderings
		allRenderings.push(ctx.getImageData(0, 0, width, height).data);
		// notify python that we have rendered one
		console.log("Drender " + millisecond)
		// needs to be put outside
		millisecond += offset
	}
	console.log("we good")
	var allImages = concateTypedArrays(Uint8Array, allRenderings);
	// each pixel will be one byte, so it works perfectly
	serverAccessableData["dweetFile"] = allImages // sends all of them concated
}

function returnAddress() {
	console.log("D" + "http://" + ip.address() + ":" + largeDataPort);
}

setup();