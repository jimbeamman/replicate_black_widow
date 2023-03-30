// All codebases are from the original work of Black Widow: Blackbox Data-driven Web Scanning by Benjamin Eriksson, Giancarlo Pellegrino†, and Andrei Sabelfeld
// Source: https://github.com/SecuringWeb/BlackWidow retrived in March, 2023

(function(proxied) {
  window.alert = function() { };
})(window.alert);

(function(proxied) {
  window.confirm = function() { return true; };
})(window.confirm);
