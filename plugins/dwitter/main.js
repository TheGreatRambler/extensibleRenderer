const canvas = require("canvas");
const readline = require("readline");
const vm = require("vm");
const request = require("request");
const fs = require("fs");
const util = require("util");

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


function setupCanvasCtx() {
	return new Promise(function (resolve, reject) {
		getDweetCode().then(function (code) {
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

function getDweetCode() {
	return new Promise(function (resolve, reject) {
		request("https://www.dwitter.net/api/dweets/701/", function (error, response, body) {
			var code = JSON.parse(body).code;
			resolve(code);
		});
	});
}

setupCanvasCtx().then(function () {
	// signal python script that we are started
	console.log("started");

	// instance to listen to command line
	const rl = readline.createInterface({
		input: process.stdin,
		output: process.stdout
	});

	rl.on("line", function (line) {
		var data = line.split(" ")[1];
		switch (line.split(" ")[0]) {
			// choose based on command
			case "time":
				currentMillisecondTime = Number(data);
				break;
			case "render":
				renderAndPrint()
				break;
		}
		console.log("next");
	});
});

function renderAndPrint() {
	vmContext.t = currentMillisecondTime / 1000; // number of seconds as a float
	vmScript.runInContext(vmContext);
	var imageData = ctx.getImageData(0, 0, 1920, 1080).data;
	var realImageData = [];
	for (var i = 0; i < imageData.length; i++) {
		if (i % 4 === 0) {
			realImageData.push(imageData[i])
		}
	}
	// print the data so python script can read it
	console.log(realImageData.join("|"));
}

process.on("SIGTERM", function () {
	// can do stuff
	process.exit(0);
});