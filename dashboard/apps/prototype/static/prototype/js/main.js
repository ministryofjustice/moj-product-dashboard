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
    this.data = {};
    this.incrementLengths = ['day', 'week', 'month', 'year'];
    this.startDate = undefined;
    this.monthNames = ['','Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];

    this.getMonthData = () => {

      let monthlyBreakdowns = this.getMonthsInProject();

      monthlyBreakdowns = this.calcMonthlyData(monthlyBreakdowns);

      let monthCostTrace = this.makeMonthlyTrace(monthlyBreakdowns, 'monthCost', 'Monthly Cost', 'bar');
      let cumulCostTrace = this.makeCumulTrace(monthlyBreakdowns);

      let traces = [monthCostTrace, cumulCostTrace];

      Plotly.newPlot(this.element, traces, {showlegend: false}, {displaylogo: false});
    };

  }

  makeMonthlyTrace(monthlyBreakdowns, y_series, name, type) {

    let x_axis = [];
    let y_axis = [];

    for (let month of monthlyBreakdowns) {

      x_axis.push(this.monthNames[month.monthNum] + ' ' + month.yearNum);
      y_axis.push(month[y_series]);

    }

    let trace = {
      x: x_axis,
      y: y_axis,
      name: name,
      type: type
    };
    return trace
  }

  makeCumulTrace(monthlyBreakdowns) {

    let x_axis = [];
    let y_axis = [];
    let cumulCost = 0;
    for (let month of monthlyBreakdowns) {
      cumulCost += month.monthCost;

      x_axis.push(this.monthNames[month.monthNum] + ' ' + month.yearNum);
      y_axis.push(cumulCost);

    }

    let trace = {
      x: x_axis,
      y: y_axis,
      name: name,
      mode: 'lines'
    };
    return trace
  }

  calcMonthlyData(monthlyBreakdowns) {

    for (let i = 0; i < monthlyBreakdowns.length; i++) {

        for (let j = 0; j < this.data.days.length; j++) {

          let date = new Date(this.data.days[j]);

          if (date.getMonth() == monthlyBreakdowns[i].monthNum && date.getFullYear() == monthlyBreakdowns[i].yearNum) {


            monthlyBreakdowns[i].monthCost += parseInt( this.data.costs[j] );
            monthlyBreakdowns[i].cumulCost += monthlyBreakdowns[i].monthCost;

          }

        }
      }

    return monthlyBreakdowns;

  }

  getMonthsInProject() {

    let month = this.startDate.getMonth();
    let year = this.startDate.getFullYear();
    let thisYear = new Date().getFullYear();
    let monthlyBreakdowns = [];

    for (year; year <= thisYear; year++) {

      for (month; month <= 12; month++) {

        monthlyBreakdowns.push({
            monthNum: month,
            yearNum: year,
            monthCost: 0,
            cumulCost: 0,
            monthTimeSpent: 0
          });

      }
      month = 1;
    }
    return monthlyBreakdowns;
  }

  handleResponse(json) {

    this.startDate = new Date(json.start_date);

    this.data = json.data;
    this.getMonthData();

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


function plotProject(id) {

  const figA = document.getElementById('fig-a');
  const figB = document.getElementById('fig-b');
  const figC = document.getElementById('fig-c');
  const figD = document.getElementById('fig-d');

  const fA = new ProjectCostFigure(figA);
  const fC = new Figure(figC);
  const fB = new Figure(figB);
  const fD = new Figure(figD);

  fA.postRequestFigure('/getfig/', {projectid: id, requested_figure: 'project_cost', start_date: '2015-01-01', end_date: '2016-08-01'});
  fB.postRequestFigure('/getfig/', testRequest);
  fC.postRequestFigure('/getfig/', testRequest);
  fD.postRequestFigure('/getfig/', testRequest);
};

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
  plotProject(projectId);
  // dropdown project selector
  $('#projects').select2().on("select2:select", (e) => {
    loadProject(e.params.data.id);
  });
})
