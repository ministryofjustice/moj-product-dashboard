import moment from 'moment';
import Plotly from './plotly-custom';

import { endOfMonth, round } from './utils';

/**
 * plot the graph for a project's monthly spendings
 */
export function plotMonthlySpendings(project, startDate, endDate, elem) {
  const monthly = project.monthlyFinancials;
  const months = Object.keys(monthly).sort()
    .filter(m => endOfMonth(m) >= startDate && endOfMonth(m) <= endDate);

  const currentMonth = moment().format('YYYY-MM');
  const pastMonths = months.filter(m => m < currentMonth);
  const futureMonths = months.filter(m => m >= currentMonth);
  const pastTotalCosts = pastMonths.map(
      m => monthly[m].total);
  const futureTotalCosts = futureMonths.map(
      m => monthly[m].total);

  // NOTE: those lines for ie9 is related to this issue
  // https://github.com/plotly/plotly.js/issues/166
  const toLabel = m => moment(m, 'YYYY-MM').format('MMM YY');
  const actualTrace = {
    x: pastMonths.map(toLabel),
    y: pastTotalCosts.map(round),
    name: 'Actual spend',
    type: 'bar',
    marker: {
      color: '#c0c2dc',
      line: {width: 0}  // for ie9 only
    }
  };
  const forecastTrace = {
    x: futureMonths.map(toLabel),
    y: futureTotalCosts.map(round),
    name: 'Forecast spend',
    type: 'bar',
    marker: {
      color: '#add1d1',
      line: {width: 0}  // for ie9 only
    }
  };
  const layout = {
    // title: 'Monthly expenditure',
    font: {
      family: 'nta'
    },
    barmode: 'stack',
    yaxis: {
      tickprefix: '\u00a3'
    },
    legend: {
      yanchor: 'top'
    },
    margin: {
      t: 20,
      l: 50,
      r: 50
    }
  };
  const data = [ actualTrace, forecastTrace ];
  Plotly.newPlot(elem, data, layout, { displayModeBar: false });
}
