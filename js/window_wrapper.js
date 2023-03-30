// All codebases are from the original work of Black Widow: Blackbox Data-driven Web Scanning by Benjamin Eriksson, Giancarlo Pellegrino†, and Andrei Sabelfeld
// Source: https://github.com/SecuringWeb/BlackWidow retrived in March, 2023

//timingCallbackWrap(window, "open", 0, openWrapper);

window["open"] = function() {
    openWrapper(this, arguments);
}



//timingCallbackWrap(window, "setInterval", 0, intervallWrapper);
