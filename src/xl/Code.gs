var api_key = "";
const INDICATOR_FIELDS = ["fullName", "version", "overview", "position", "status"];

function myFunction() {
  Logger.log(101);
  return 4;
}

async function MLKey(key) {
  api_key = key;
  Logger.log("api_key is " + api_key);
  return "OK";
}

async function MLIndicators() {
  Logger.log("Global api_key: " + api_key);
  if (api_key == null || api_key.length < 1) {
    api_key = PropertiesService.getScriptProperties().getProperty('API_KEY');  
    Logger.log("Properties api_key: " + api_key);
  }
  const url = "https://qa1.marcuslion.com/core/api/v2/indicators";
  var data = {}
  exportMap = new Map();
  var options = {
    'method' : 'get',
    'headers' : {'contentType': 'application/json','X-MARCUSLION-API-KEY': api_key}
  };
  var response = UrlFetchApp.fetch(url, options);
  var json = response.getContentText();
  var obj = JSON.parse(json);
  var arr = Array.from(obj);
  //var firstObj = arr[0];
  arr.forEach((thisObj) => {
    var version = thisObj['version'];
    var name = thisObj['name'];
    Logger.log("version is " + version);
    var keys = Object.keys(thisObj);
    Logger.log("keys is " + keys);
    keys.forEach((el) => {
      var strEl = el.toString();
      var val = thisObj[el];
      if (strEl.indexOf('Image') < 1)
        Logger.log(strEl + ": " + val);

      if (INDICATOR_FIELDS.includes(strEl))
        exportMap.set(name + '.' + strEl, val);
    });
  });

  return Array.from(exportMap);
}

