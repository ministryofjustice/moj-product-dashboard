import 'whatwg-fetch';
import Cookies from 'js-cookie';
import Plotly from 'plotly.js/lib/core';
import * as bar from 'plotly.js/lib/bar';
Plotly.register([bar]);

import $ from 'jquery';
import select2 from 'select2';
import URI from 'urijs';

require('select2/dist/css/select2.min.css');
require('../styles/gov-uk-elements.css');
require('../styles/main.css');


class Figure {

  constructor(element) {
    // if (new.target === Figure) {
    //   throw new TypeError("Figure class is abstract and should not be instantiated");
    // }
    this.element = element;
    this.data = {};
    this.traces = [];
  }

  plot() {
    Plotly.newPlot(this.element, this.traces, {displaylogo: false});
  }

  newTrace() {
    return { x: [], y: [], name: 'No Name', type: 'bar'}
  }

  handleResponse(json) {
    this.data = json;
    console.log(this.data)
  }

  getRequestFigure (url) {
    fetch(url)
      .then((response) => response.json())
      .then((json) => this.handleResponse(json));
  }

  postRequestFigure (url, requestJson) {
    // console.log(requestJson);
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


class SingleProjectFigure extends Figure {

  constructor(element) {
    super(element);
  }

  handleResponse(json) {
    super.handleResponse(json);
    this.makeTraces();
    this.plot();

  }

  makeTraces() {

    let costTrace = this.newTrace();

    for (let timeWindow of this.data) {

      costTrace.x.push(timeWindow.label);
      costTrace.y.push(timeWindow.cost);

    }

    this.traces.push(costTrace);

  }


}


var testRequest = {
  requested_figure : 'staff_split',
  projectids : [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
  persons : [],
  areas : [],
  start_date: '2015-01-01',
  end_date: '2016-05-23'
};


var projectTestRequest = {

  request_type : 'single_project',
  project_id : 52,
  start_date: '2015-01-01',
  end_date: '2016-06-01',
  time_increment: 'day',
  filter_empty: true

};


function plot() {

  const figA = document.getElementById('fig-a');
  const figB = document.getElementById('fig-b');
  const figC = document.getElementById('fig-c');

  const fA = new SingleProjectFigure(figA);
  // const fB = new MonthCumulFigure(figB);
  // const fC = new StaffSplitFigure(figC);

  // console.log(document.getElementById('projects').value);

  // fA.postRequestFigure('/getdata/', projectTestRequest);
  // fB.postRequestFigure('/getdata/', projectTestRequest);
  // fC.postRequestFigure('/getdata/', projectTestRequest);

  fA.postRequestFigure('/getdata/', projectTestRequest)

}


/**
 * get projectId based on the query string
 */
function getProjectId() {
  const projectId = URI(window.location.href).query(true).projectid;
  console.log('projectId:', projectId);
  return projectId;
};


function loadProject(id) {
  const url = [location.protocol, '//', location.host, location.pathname].join('');

  window.location.href = url + '?projectid=' + id;
};



$(() => {
  const projectId = getProjectId();
  // plot project
  plot();
  // dropdown project selector
  $('#projects').select2().on("select2:select", (e) => {
    loadProject(e.params.data.id);
  });
})
