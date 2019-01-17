const canvas = require("canvas");

function serializeArrayBuffer(theBuffer, chunks) {
	var dataArray = new Uint16Array(theBuffer);

	function chunk(arr, len) {

		var chunks = [],
			i = 0,
			n = arr.length;

		while (i < n) {
			// works with typed arrays too
			chunks.push(arr.slice(i, i += len));
		}

		return chunks;
	}
	var returnString = "";
	chunk(dataArray, chunks).forEach(function(element) {
		returnString += String.fromCharCode.apply(null, element);
	});
	return returnString;
}

function unserializeArrayBuffer(str) {
	var buf = new ArrayBuffer(str.length * 2); // 2 bytes for each char
	var bufView = new Uint16Array(buf);
	for (var i = 0, strLen = str.length; i < strLen; i++) {
		bufView[i] = str.charCodeAt(i);
	}
	return buf;
}

const theCanvas = canvas.createCanvas(1920, 1080);
const ctx = theCanvas.getContext("2d");
// From a local file path:
const img = new canvas.Image()
img.onload = function() {
	ctx.drawImage(img, 0, 0);
	var data = ctx.getImageData(0, 0, theCanvas.width, theCanvas.height);
	console.log(data.data.length);
	for (var i = 1; i < 500; i++) {
		var chunkNum = i * 100;
		console.log("Start: " + chunkNum);
		console.time("serialize " + chunkNum);
		var serializedString = serializeArrayBuffer(data.data.buffer, chunkNum);
		console.log(chunkNum + ": serializedLength " + serializedString.length);
		var arrayBuf = unserializeArrayBuffer(serializedString);
		console.timeEnd("serialize " + chunkNum);
	}
};
img.onerror = err => {
	throw err
}
img.src = "test.jpg";