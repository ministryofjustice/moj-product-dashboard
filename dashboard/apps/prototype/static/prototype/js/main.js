import 'whatwg-fetch';
import Cookies from 'js-cookie';
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

  handleResponse(json) {
    console.log('handleResponse called');
    this.data = json.data;
    this.layout = json.layout;
    this.plot();
  }

  getRequestFigure (url) {
    fetch(url)
      .then((response) => response.json())
      .then((json) => this.handleResponse(json));
  }

  postRequestFigure (url) {
    fetch(url, {
      credentials: 'same-origin',
      method: 'POST',
      headers: {
        'X-CSRFToken': Cookies.get('csrftoken'),
        'Accept': 'application/json',
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        test: 'testtext',
      })
    })
    .then((response) => response.json())
      .then((json) => this.handleResponse(json));
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

  fA.getRequestFigure('/comp/');
  fB.postRequestFigure('/getrand/');
  fC.getRequestFigure('/getrand/');
  fD.getRequestFigure('/getrand/');
}

document.addEventListener("DOMContentLoaded", () => onLoad());
