import 'whatwg-fetch';
import Plotly from 'plotly.js';

class Figure {

  constructor(element) {
    this.element = element;
    this.data = {};
    this.layout = {};
  }

  plot() {
    Plotly.newPlot(this.element, this.data, this.layout, {displaylogo: false});
  }

  getFigure () {
    fetch('/getfig/')
      .then((response) => response.json())
      .then((json) => {
        this.data = json.data;
        this.layout = json.layout;
        this.plot();
      });
  }
};

//Run on page load
function onLoad() {
  const topLeft = document.getElementById("top_left");
  const topRight = document.getElementById("top_right");
  const bottomLeft = document.getElementById("bottom_left");
  const bottomRight = document.getElementById("bottom_right");

  const tL = new Figure(topLeft);
  const tR = new Figure(topRight);
  const bL = new Figure(bottomLeft);
  const bR = new Figure(bottomRight);

  tL.getFigure();
  tR.getFigure();
  bL.getFigure();
  bR.getFigure();
};

document.addEventListener("DOMContentLoaded", () => onLoad());
