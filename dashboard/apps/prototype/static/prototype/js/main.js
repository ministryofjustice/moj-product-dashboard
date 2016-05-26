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
    this.data = json.data;
    this.layout = json.layout;
    this.plot();
  }

  getRequestFigure (url) {
    fetch(url)
      .then((response) => response.json())
      .then((json) => this.handleResponse(json));
  }

  postRequestFigure (url, requestJson) {
    fetch(url, {
      credentials: 'same-origin',
      method: 'POST',
      headers: {
        'X-CSRFToken': Cookies.get('csrftoken'),
        'Accept': 'application/json',
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(requestJson)
    })
    .then((response) => response.json())
      .then((json) => this.handleResponse(json));
  }

}

class ProjectCostFigure extends Figure {

  constructor(element) {
    super(element);
    this.rawData = {}
  }

  handleResponse(json) {

    this.rawData = json;
    console.log(json)
    // Something here
  }



}

var testRequest = {

  requested_figure : 'staff_split',

  projects : ['Digital'],

  persons : [],

  areas : [],

  start_date: '2015-01-01',

  end_date: '2016-05-23'

};

var projectTestRequest = {

  requested_figure : 'project_cost',

  projects : ['CLA Public'],

  persons : [],

  areas : [],

  start_date: '2015-01-01',

  end_date: '2016-05-23'

};


//Run on page load
function onLoad() {
  const figA = document.getElementById('fig-a');
  const figB = document.getElementById('fig-b');
  const figC = document.getElementById('fig-c');
  const figD = document.getElementById('fig-d');

  const fA = new Figure(figA);
  const fB = new Figure(figB);
  const fC = new ProjectCostFigure(figC);
  const fD = new Figure(figD);

  fA.getRequestFigure('/comp/');
  fB.postRequestFigure('/getfig/', testRequest);
  fC.getRequestFigure('/getfig/', projectTestRequest);
  fD.getRequestFigure('/getrand/');
}

document.addEventListener("DOMContentLoaded", () => onLoad());
