/**
 * Created by jamesnarey on 17/05/2016.
 */


function figure(element) {
  this.element = element;

  this.getFigure = function () {
    console.log("Request made");
    var element = this.element;
    $.ajax({
      url: "/getfig/",
      type: "GET",

      success: function (json) {

        Plotly.newPlot(element, json);

      },

      error: function (xhr, errmsg, err) {
        console.log(xhr.status + ": " + xhr.responseText);
      }

    });
  }
}

//function getFigure () {
//  console.log("Get statuses request made");
//  $.ajax({
//    url: "/getfig/",
//    type: "GET",
//
//    success: function (json) {
//
//      Plotly.newPlot(element, json);
//
//    },
//
//    error: function (xhr, errmsg, err) {
//      console.log(xhr.status + ": " + xhr.responseText);
//    }
//
//  });
//}

//Run on page load
$(document).ready(function () {

  var topLeft = document.getElementById("top_left");
  var topRight = document.getElementById("top_right");
  var bottomLeft = document.getElementById("bottom_left");
  var bottomRight = document.getElementById("bottom_right");

  //getFigure(topLeft);
  //getFigure(topRight);
  //getFigure(bottomLeft);
  //getFigure(bottomRight);

  var tL = new figure(topLeft);
  var tR = new figure(topRight);
  var bL = new figure(bottomLeft);
  var bR = new figure(bottomRight);

  tL.getFigure();
  tR.getFigure();
  bL.getFigure();
  //bR.getFigure();

});

