/**
 * Created by jamesnarey on 17/05/2016.
 */

// This doesn't work:
//var nodeDir = "../../../../../../node_modules/";
//require(nodeDir + "whatwg-fetch");


require("whatwg-fetch");
var Plotly = require("plotly.js");


class figure {

  constrctor(element) {
    this.element = element;
    this.data = {};
    this.layout = {};
  }

  plot() {

    Plotly.newPlot(this.element, this.data, this.layout, {displaylogo: false});

  }

  getFigure () {

    console.log("Request made");

    var $this = this;

    fetch('/getfig/')
      .then(function (response) {
        return response.json()
      }).then(function (json) {

      $this.data = json.data;
      $this.layout = json.layout;
      $this.plot();
    });

  }
}


//function figure(element) {
//  this.element = element;
//  this.data = {};
//  this.layout = {};
//  this.type = 'line';
//
//  this.plot = function () {
//
//    Plotly.newPlot(this.element, this.data, this.layout, {displaylogo: false});
//
//  };
//  this.getFigure = function () {
//
//    console.log("Request made");
//
//    var $this = this;
//
//    fetch('/getfig/')
//      .then(function (response) {
//        return response.json()
//      }).then(function (json) {
//
//      $this.data = json.data;
//      $this.layout = json.layout;
//      $this.plot();
//    });
//
//  }
//}


//Run on page load
$(document).ready(function () {

  var topLeft = document.getElementById("top_left");
  var topRight = document.getElementById("top_right");
  var bottomLeft = document.getElementById("bottom_left");
  var bottomRight = document.getElementById("bottom_right");

  var tL = new figure(topLeft);
  var tR = new figure(topRight);
  var bL = new figure(bottomLeft);
  var bR = new figure(bottomRight);

  tL.getFigure();
  tR.getFigure();
  bL.getFigure();
  //bR.getFigure();

});

