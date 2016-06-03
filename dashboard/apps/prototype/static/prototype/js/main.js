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
    this.layout = {showlegend: true}
    this.traces = [];
  }

  plot() {
    Plotly.newPlot(this.element, this.traces, this.layout, {displaylogo: false});
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
    this.traceTypes = [];
  }

  handleResponse(json) {
    super.handleResponse(json);
    SingleProjectFigure.data = json;
    this.makeTraces();
    this.plot();
  }

  makeTraces() {

    if (this.traceTypes.indexOf('staff_split') > -1) {
      this.makeTrace('cs_perc', '% Civil Servants');
      this.makeTrace('contr_perc', '% Contractors');
      this.layout.barmode = 'stack';
      return;
    }

    if (this.traceTypes.indexOf('cost') > -1) { this.makeTrace('cost', 'Monthly Cost £'); }
    if (this.traceTypes.indexOf('time') > -1) { this.makeTrace('time', 'Person Days'); }
    if (this.traceTypes.indexOf('cumulative') > -1) { this.makeTrace('cumul_cost', 'Cumulative Cost £', 'line'); }

    console.log(this.traces);


  }

  updateData(url) {
    console.log('>>>Requesting data');
    this.postRequestFigure(url, SingleProjectFigure.requestData);
  }

  init(url, traceTypes) {
    this.traceTypes = traceTypes;
    if (SingleProjectFigure.data != {}) {
      this.updateData(url);
    }
    else {
      console.log('>>>Using stored data');
      this.plot();
    }
  }

  // makeCostTrace() {
  //
  //   let costTrace = this.newTrace();
  //
  //   for (let timeWindow of SingleProjectFigure.data) {
  //
  //     costTrace.x.push(timeWindow.label);
  //     costTrace.y.push(timeWindow.cost);
  //
  //   }
  //
  //   this.traces.push(costTrace);
  //
  // }

  makeTrace(key, name, type='bar') {

    let trace = this.newTrace();
    trace.name = name;
    trace.type = type;

    for (let timeWindow of SingleProjectFigure.data) {

      trace.x.push(timeWindow.label);
      trace.y.push(timeWindow[key]);

    }
    this.traces.push(trace);
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
  const figB = document.getElementById('fig-b');
  const figC = document.getElementById('fig-c');

  const fA = new SingleProjectFigure(figA);
  const fB = new SingleProjectFigure(figB);
  const fC = new SingleProjectFigure(figC);

  fA.init('/getdata/', ['cost', 'cumulative', 'time']);
  fB.init('/getdata/', ['time']);
  fC.init('/getdata/', ['staff_split']);

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
