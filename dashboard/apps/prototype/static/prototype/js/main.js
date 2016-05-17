/**
 * Created by jamesnarey on 17/05/2016.
 */


function figure(element) {
  this.element = element;
  this.data = {};
  this.layout = {};

  this.plot = function () {

    Plotly.newPlot(this.element, this.data, this.layout, {displaylogo: false});

  };
  this.getFigure = function () {

    console.log("Request made");
    var $this = this;
    $.ajax({
      url: "/getfig/",
      type: "GET",

      success: function (json) {
        $this.data = json.data;
        $this.layout = json.layout;
        $this.plot();

      },

      error: function (xhr, errmsg, err) {
        console.log(xhr.status + ": " + xhr.responseText);
      }

    });
  }
}


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

