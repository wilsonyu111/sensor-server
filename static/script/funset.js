function updateSliderPWM(element) {
  const sliderValue = document.getElementById("pwmSlider").value;
  document.getElementById("textSliderValue").innerHTML = sliderValue;
  const request = new XMLHttpRequest();
  request.open("GET", "/slider?value=" + sliderValue, true);
  request.send();
}

function autoMode(element) {
  const request = new XMLHttpRequest();
  request.open("GET", "/mode?value=auto", true);
  request.send();
  document.getElementById("current_mode").innerHTML = "curtain mode: auto";
}

function manualMode(element) {
  const request = new XMLHttpRequest();
  request.open("GET", "/mode?value=manual", true);
  request.send();
  document.getElementById("current_mode").innerHTML = "curtain mode: manual";
}

function updatePageValue(element) {
  const request = new XMLHttpRequest();
  request.addEventListener("readystatechange", () => {
    // in async request, ready state 4 is when the request is fully done
    // look at xml readystatechange for what each code means
    if (request.readyState === 4) {
      const data = request.responseText;
      const dataMap = new Map(Object.entries(JSON.parse(data)));
      // console.log(dataMap);
      dataMap.forEach((value, key) => {
        console.log(value, key); // 👉️ Chile country, 30 age
      });
      // document.getElementById("textSliderValue").innerHTML =
      //   dataMap.get("curtain_position");
      // document.getElementById("current_mode").innerHTML =
      //   "current mode: " + dataMap.get("curtain_mode");
      // document.getElementById("pwmSlider").value = parseInt(
      //   dataMap.get("curtain_position")
      // );
    }
  });
  request.open("GET", "/getData", true);
  request.send();
}

// function makeParagraphTag(statMap)
// {
//   let para = document.createElement("div");
//   var node = document.createTextNode("Tutorix is the best e-learning platform");
//   para.appendChild(node);
//   var element = document.getElementById("new");
//   element.appendChild(para);
// }

function makeTag(tag_name, class_name = "")
{
  let tag = document.createElement(tag_name);
  
  if (class_name != "")
    tag.className = class_name;
    
  return tag
}
function addNewNode(statMap)
{
  // temperature: 123, hudmidity: 9999, last active: '2022/09/03 05:58 PM', location: '2'
  div1 = makeTag("div", "info_container")
  tempDiv = makeTag statMap.get("temperature")
}
