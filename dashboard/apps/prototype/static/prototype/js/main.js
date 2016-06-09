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


/**
 * send a POST request to the backend to retrieve project profile
 */
function getProjectData(id) {
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
}

/**
 * parse the financial infomation about the project
 */
function parseProjectFinancials(financial) {
  let [months, costs] = _(financial).toPairs().sort().unzip().value();
  months = months.map(m => moment(m, 'YYYY-MM').format('MMM YY'));

  const _mapFloat = key => costs.map(c => parseFloat(c[key]));
  const contractorCosts = _mapFloat('contractor');
  const civilServantCosts = _mapFloat('non-contractor');
  const additionalCosts = _mapFloat('additional');
  const budget = _mapFloat('budget');
  
  const totalCosts = _.zip(contractorCosts, civilServantCosts, additionalCosts)
                      .map(([x, y, a]) => x + y + a);
  const totalCostsCumulative = [];
  totalCosts.reduce((x, y, i) => totalCostsCumulative[i] = x + y, 0);

  return {
    months,
    budget,
    civilServantCosts,
    contractorCosts,
    additionalCosts,
    totalCostsCumulative
  };
}

/**
 * plot the graphs for a project
 */
function plotProject(project, elem) {
  const financial = parseProjectFinancials(project.financial);
  const months = financial.months;

  const civilServiceTrace = {
    x: months,
    y: financial.civilServantCosts,
    name: 'Civil Servant',
    type: 'bar',
    marker: {
      color: '#c0c2dc'
    }
  };
  const contractorTrace = {
    x: months,
    y: financial.contractorCosts,
    name: 'Contractor',
    type: 'bar',
    marker: {
      color: '#b5d8df'
    }
  };
  const additionalTrace = {
    x: months,
    y: financial.additionalCosts,
    name: 'additional',
    type: 'bar',
    marker: {
      color: '#B2CFB2'
    }
  };
  const totalCostTrace = {
    x: months,
    y: financial.totalCostsCumulative,
    name: 'Cumulative',
    mode: 'lines',
    yaxis: 'y2',
    marker: {
      color: '#6F777B'
    }
  };
  const budgetTrace = {
    x: months,
    y: financial.budget,
    name: 'Budget',
    mode: 'lines',
    yaxis: 'y2',
    marker: {
      color: '#F0E891'
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
      elem,
      [civilServiceTrace, contractorTrace, additionalTrace, totalCostTrace,
       budgetTrace],
      layout);
}


/**
 * get projectId based on the query string
 */
function getProjectId() {
  return URI(window.location.href).query(true).projectid;
}


/**
 * load the page for the project based on id
 **/
function loadProjectPage(id) {
  const url = [location.protocol, '//', location.host, location.pathname].join('');
  window.location.href = url + '?projectid=' + id;
}

  
$(() => {
  // get the DOM element for the graph
  const elem = document.getElementById('fig-a');
  // get the projectId
  const projectId = getProjectId();
  // plot the project
  getProjectData(projectId)
    .then(projectData => plotProject(projectData, elem));

  // dropdown project selector
  $('#projects').select2().on("select2:select", (e) => {
    loadProjectPage(e.params.data.id);
  });
});
