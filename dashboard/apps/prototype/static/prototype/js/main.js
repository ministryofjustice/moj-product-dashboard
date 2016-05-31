import 'whatwg-fetch';
import Cookies from 'js-cookie';
import Plotly from 'plotly.js/lib/core';
import * as bar from 'plotly.js/lib/bar';
Plotly.register([bar]);

import $ from 'jquery';
import select2 from 'select2';

require('select2/dist/css/select2.min.css');
require('../styles/gov-uk-elements.css');
require('../styles/main.css');


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

var testRequest = {
  requested_figure : 'staff_split',
  projects : ['Digital'],
  persons : [],
  areas : [],
  start_date: '2015-01-01',
  end_date: '2016-05-23'
};

function plot() {
  const figA = document.getElementById('fig-a');
  const figB = document.getElementById('fig-b');
  const figC = document.getElementById('fig-c');
  const figD = document.getElementById('fig-d');

  const fA = new Figure(figA);
  const fB = new Figure(figB);
  const fC = new Figure(figC);
  const fD = new Figure(figD);

  fA.getRequestFigure('/comp/');
  fB.postRequestFigure('/getfig/', testRequest);
  fC.getRequestFigure('/getrand/');
  fD.getRequestFigure('/getrand/');
};

function selectProject(projectId) {
  const url = [location.protocol, '//', location.host, location.pathname].join('');
  window.location.href = url + '?projectid=' + projectId;
};

$(() => {
  // plot
  plot();
  // dropdown project selector
  $('#projects').select2().on("select2:select", (e) => {
    const projectId = e.params.data.id;
    selectProject(projectId);
  });
})

