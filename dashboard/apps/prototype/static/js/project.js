import 'whatwg-fetch';
import moment from 'moment';
import Griddle from 'griddle-react';
import React from 'react';

import Plotly from './plotly-custom';

/**
 * send a POST request to the backend to retrieve project profile
 */
export function getProjectData(id, csrftoken) {
  const init = {
    credentials: 'same-origin',
    method: 'POST',
    headers: {
      'X-CSRFToken': csrftoken,
      'Accept': 'application/json',
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({id: id})
  };
  return fetch('/project.json', init)
    .then(response => response.json());
}

/**
 * parse the financial infomation about the project
 */
export function parseProjectFinancials(financial) {
  const _months = Object.keys(financial).sort();
  const costs = _months.map(month => financial[month]);
  const months = _months.map(m => moment(m, 'YYYY-MM').format('MMM YY'));

  const mapFloat = key => costs.map(c => parseFloat(c[key]));
  const contractorCosts = mapFloat('contractor');
  const civilServantCosts = mapFloat('non-contractor');
  const staffCosts = contractorCosts
    .map((cost, index) => cost + civilServantCosts[index]);
  const additionalCosts = mapFloat('additional');
  const budget = mapFloat('budget');

  const totalCosts = months.map(
    (month, i) => contractorCosts[i] + civilServantCosts[i] + additionalCosts[i]);
  const totalCostsCumulative = [];
  let cumulative = 0;
  totalCosts.map(costs => {
    cumulative += costs;
    totalCostsCumulative.push(cumulative);
  });

  return {
    months,
    budget,
    civilServantCosts,
    contractorCosts,
    staffCosts,
    additionalCosts,
    totalCostsCumulative
  };
}


/**
 * plot the graphs for a project
 */
export function plotProject(project, elem) {
  const financial = parseProjectFinancials(project.financial);
  const months = financial.months;

  // NOTE: those lines for ie9 is related to this issue
  // https://github.com/plotly/plotly.js/issues/166
  const staffTrace = {
    x: months,
    y: financial.staffCosts,
    name: 'Staff',
    type: 'bar',
    marker: {
      color: '#c0c2dc',
      line: {width: 0}  // for ie9 only
    }
  };
  const additionalTrace = {
    x: months,
    y: financial.additionalCosts,
    name: 'Additional',
    type: 'bar',
    marker: {
      color: '#b5d8df',
      line: {width: 0}  // for ie9 only
    }
  };
  const totalCostTrace = {
    x: months,
    y: financial.totalCostsCumulative,
    name: 'Cumulative',
    mode: 'lines',
    yaxis: 'y2',
    marker: {
      color: '#6F777B',
      line: {width: 0}  // for ie9 only
    }
  };
  const budgetTrace = {
    x: months,
    y: financial.budget,
    name: 'Budget',
    mode: 'lines',
    yaxis: 'y2',
    marker: {
      color: '#FFBF47',
      line: {width: 0}  // for ie9 only
    }
  };
  const layout = {
    title: project.name,
    font: {
      family: 'nta'
    },
    barmode: 'stack',
    yaxis: {
      title: 'monthly cost',
      tickprefix: '\u00a3'
    },
    yaxis2: {
      title: 'cumulative',
      overlaying: 'y',
      side: 'right',
      rangemode: 'tozero',
      tickprefix: '\u00a3'
    },
    legend: {
      yanchor: 'bottom'
    }
  };
  const data = [
    staffTrace,
    additionalTrace,
    totalCostTrace,
    budgetTrace
  ];
  Plotly.newPlot(elem, data, layout);
}


/**
 * React component for a table of projects
 */
export const ProjectsTable = ({projects}) => {

  const displayMoney = (props) => {
    const number = Number(Number(props.data).toFixed(0))
      .toLocaleString();
    return (<span>£{number}</span>);
  };

  const columnMetadata = [
    {
      'columnName': 'name',
      'order': 1,
      'displayName': 'Project name',
      'customComponent': (props) => (
        <a href={`/projects/${props.rowData.id}`}>
          {props.data}
        </a>
      ),
    },
    {
      'columnName': 'rag',
      'order': 2,
      'displayName': 'RAG',
    },
    {
      'columnName': 'team_size',
      'order': 3,
      'displayName': 'Team size',
      'customCompareFn': Number,
      'customComponent': (props) => (
        <span>
          {Number(props.data).toFixed(1)}
        </span>),
    },
    {
      'columnName': 'cost_to_date',
      'order': 4,
      'displayName': 'Cost to date',
      'customCompareFn': Number,
      'customComponent': displayMoney,
    },
    {
      'columnName': 'budget',
      'order': 5,
      'displayName': 'Budget',
      'customCompareFn': Number,
      'customComponent': displayMoney,
    }
  ];

  return (
    <Griddle
      results={projects}
      columns={columnMetadata.map(item => item['columnName'])}
      columnMetadata={columnMetadata}
      useGriddleStyles={false}
      bodyHeight={800}
      resultsPerPage={100}
    />
  );
}
