import $ from 'jquery';
import select2 from 'select2';
import Plotly from './custom-plotly';
import {getProjectId, loadProjectPage, parseProjectFinancials, getProjectData} from './project';

require('select2/dist/css/select2.min.css');
require('../styles/gov-uk-elements.css');
require('../styles/main.css');

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
