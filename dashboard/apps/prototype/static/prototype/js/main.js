import 'whatwg-fetch';
import Plotly from 'plotly.js/lib/core';
import * as bar from 'plotly.js/lib/bar';

Plotly.register([bar]);

class Figure {

  constructor(element) {
    this.element = element;
    this.data = {};
    this.layout = {};
  }

  plot() {
    Plotly.newPlot(this.element, this.data, this.layout, {displaylogo: false});
  }

  getFigure (url) {
    fetch(url)
      .then((response) => response.json())
      .then((json) => {
        this.data = json.data;
        this.layout = json.layout;
        this.plot();
      });
  }
}

//Run on page load
function onLoad() {
  const figA = document.getElementById("fig-a");
  const figB = document.getElementById("fig-b");
  const figC = document.getElementById("fig-c");
  const figD = document.getElementById("fig-d");

  const fA = new Figure(figA);
  const fB = new Figure(figB);
  const fC = new Figure(figC);
  const fD = new Figure(figD);

  fA.getFigure('/comp/');
  fB.getFigure('/getfig/');
  fC.getFigure('/getfig/');
  fD.getFigure('/getfig/');
}

document.addEventListener("DOMContentLoaded", () => onLoad());
