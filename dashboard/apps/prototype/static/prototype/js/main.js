import 'whatwg-fetch';
import Cookies from 'js-cookie';
import Plotly from 'plotly.js/lib/core';
import * as bar from 'plotly.js/lib/bar';
Plotly.register([bar]);

import $ from 'jquery';
import select2 from 'select2';
import URI from 'urijs';
import _ from 'lodash';
import moment from 'moment';

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

// TODO this function needs some structure
function plotProject(project) {
  const costs = _.toPairs(project.financial).sort();
  const months = _.map(
      costs, ([k, v]) => moment(k, 'YYYY-MM').format('MMM YY'));
  const contractorCosts = _.map(
      costs, ([k, v]) => parseFloat(v['contractor']));
  const civilServantCosts = _.map(
      costs, ([k, v]) => parseFloat(v['non-contractor']));
  const additionalCosts = _.map(
      costs, ([k, v]) => parseFloat(v['additional']));
  const totalCosts = _.map(
      _.zip(contractorCosts, civilServantCosts, additionalCosts),
      ([x, y, a]) => x + y + a);
  const totalCostsCumulative = [];
  totalCosts.reduce((x, y, i) => totalCostsCumulative[i] = x + y, 0);
  const budget = _.map(
      costs, ([k, v]) => parseFloat(v['budget']));
  const civilServiceTrace = {
    x: months,
    y: civilServantCosts,
    name: 'Civil Servant',
    type: 'bar',
    marker: {
      color: '#c0c2dc'
    }
  };
  const contractorTrace = {
    x: months,
    y: contractorCosts,
    name: 'Contractor',
    type: 'bar',
    marker: {
      color: '#b5d8df'
    }
  };
  const additionalTrace = {
    x: months,
    y: additionalCosts,
    name: 'additional',
    type: 'bar',
    marker: {
      color: '#B2CFB2'
    }
  };
  const totalCostTrace = {
    x: months,
    y: totalCostsCumulative,
    name: 'Cumulative',
    mode: 'lines',
    yaxis: 'y2',
    marker: {
      color: '#6F777B'
    }
  };
  const budgetTrace = {
    x: months,
    y: budget,
    name: 'Budget',
    mode: 'lines',
    yaxis: 'y2',
    marker: {
      color: '#FFBF47'
    }
  };
  const layout = {
    title: project.name,
    barmode: 'stack',
    yaxis: {
      title: 'monthly cost'
    },
    yaxis2: {
      title: 'cumulative',
      overlaying: 'y',
      side: 'right'
    },
    legend: {
      yanchor: 'bottom'
    }
  };
  Plotly.newPlot(
      document.getElementById('fig-a'),
      [civilServiceTrace, contractorTrace, additionalTrace, totalCostTrace,
        budgetTrace],
      layout);
};

function getProjectJSON(id) {
  return fetch('/project.json', {
    credentials: 'same-origin',
    method: 'POST',
    headers: {
      'X-CSRFToken': Cookies.get('csrftoken'),
      'Accept': 'application/json',
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({projectid: id})
  }).then(response => response.json());
};

/**
 * get projectId based on the query string
 */
function getProjectId() {
  return URI(window.location.href).query(true).projectid;
};


function loadProject(id) {
  const url = [location.protocol, '//', location.host, location.pathname].join('');
  window.location.href = url + '?projectid=' + id;
};


$(() => {
  const projectId = getProjectId();
  // plot project
  getProjectJSON(projectId)
    .then(plotProject);
  // dropdown project selector
  $('#projects').select2().on("select2:select", (e) => {
    loadProject(e.params.data.id);
  });
})
