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

class ProjectCostFigure extends Figure {

  constructor(element) {
    super(element);
    this.data = {};
    this.initialEndDate = new Date();
    this.incrementLengths = ['day', 'week', 'month', 'year'];
    this.incrementLength = this.incrementLengths[3];
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
            console.log('match');

            monthlyBreakdowns[i].monthCost += parseInt( this.data.costs[j] );
            monthlyBreakdowns[i].cumulCost += monthlyBreakdowns[i].monthCost;

          }

        }
        console.log(monthlyBreakdowns[i].monthNum + ' ' + monthlyBreakdowns[i].yearNum + ' ' + monthlyBreakdowns[i].monthCost + ' ' + monthlyBreakdowns[i].cumulCost);

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

    this.endDate = new Date(json.end_date);
    this.startDate = new Date(json.start_date);

    this.data = json.data;
    console.log(this.data);
    this.getMonthData();

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
// function onLoad() {
// =======
function plot() {

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
  fC.postRequestFigure('/getfig/', projectTestRequest);
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

