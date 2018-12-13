var instructionQueue = [];

self.onerror = function(e) {
  var data = e.data;
  switch (data.instructionType) {
    case "kill":
      break;
  }
};
