import 'whatwg-fetch';
import URI from 'urijs';
import moment from 'moment';
import _ from 'lodash';
import Plotly from './plotly-custom';

/**
 * send a POST request to the backend to retrieve project profile
 */
export function getProjectData(id, csrftoken) {
  return fetch('/project.json', {
    credentials: 'same-origin',
    method: 'POST',
    headers: {
      'X-CSRFToken': csrftoken,
      'Accept': 'application/json',
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({projectid: id})
  }).then(response => response.json());
}

/**
 * parse the financial infomation about the project
 */
export function parseProjectFinancials(financial) {
  const [_months, costs] = _(financial).toPairs().sort().unzip().value();
  const months = _months.map(m => moment(m, 'YYYY-MM').format('MMM YY'));

  const mapFloat = key => costs.map(c => parseFloat(c[key]));
  const contractorCosts = mapFloat('contractor');
  const civilServantCosts = mapFloat('non-contractor');
  const additionalCosts = mapFloat('additional');
  const budget = mapFloat('budget');

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
 * get projectId based on the query string
 */
export function getProjectId(pageURL) {
  return URI(pageURL).query(true).projectid;
}


/**
 * get the page for the project based on id
 **/
export function getProjectURL(pageURL, projectid) {
  return URI(pageURL).setQuery('projectid', projectid).href();
}


/**
 * plot the graphs for a project
 */
export function plotProject(project, elem) {
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
    elem,
    [civilServiceTrace, contractorTrace, additionalTrace, totalCostTrace,
    budgetTrace],
    layout);
}
