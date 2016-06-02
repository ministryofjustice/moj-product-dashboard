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
    this.traces = [];
  }

  plot() {
    Plotly.newPlot(this.element, this.traces, {displaylogo: false});
  }

  newTrace() {
    return { x: [], y: [], name: 'No Name', type: 'bar'}
  }

  handleResponse(json) {
    console.log(json)
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
    this.traceType = undefined;
  }

  handleResponse(json) {
    super.handleResponse(json);
    SingleProjectFigure.data = json;
    this.makeTraces();
  }

  makeTraces() {

    if (this.traceType == 'cost') { this.makeCostTrace(); }
    if (this.traceType == 'cumulative') {}

    console.log('>>>>>' + this.traces);
    this.plot();

  }

  display(url, traceType) {
    this.getData(url);
    this.traceType = traceType;
  }

  updateData(url) {
    this.postRequestFigure(url, SingleProjectFigure.requestData);
  }

  getData(url) {
    if (SingleProjectFigure.data != {}) {
      this.updateData(url);
    }
    else {
      console.log('Data already aquired, use updateData to refresh');
      this.plot();
    }
  }

  makeCostTrace() {

    let costTrace = this.newTrace();

    for (let timeWindow of SingleProjectFigure.data) {

      costTrace.x.push(timeWindow.label);
      costTrace.y.push(timeWindow.cost);

    }

    this.traces.push(costTrace);

  }

}

SingleProjectFigure.data = {};

SingleProjectFigure.requestData = {

  request_type : 'single_project',
  project_id : 52,
  start_date: '2015-01-01',
  end_date: '2016-06-01',
  time_increment: 'month',
  filter_empty: false

};


function plot() {

  const figA = document.getElementById('fig-a');
  const fA = new SingleProjectFigure(figA);

  // fA.getData('/getdata/');
  fA.display('/getdata/', 'cost');

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
