// All codebases are from the original work of Black Widow: Blackbox Data-driven Web Scanning by Benjamin Eriksson, Giancarlo Pellegrino†, and Andrei Sabelfeld
// Source: https://github.com/SecuringWeb/BlackWidow retrived in March, 2023


xss_array = []

function xss(data) {
  // var oReq = new XMLHttpRequest();
  // oReq.open("GET", "http://localhost:9001/?data=" + data);
  // oReq.send();
  xss_array.push(data);
}
