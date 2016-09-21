import moment from 'moment';

import Plotly from '../libs/plotly-custom';
import { endOfMonth, round } from '../libs/utils';

/**
 * plot the graph for a product's monthly spendings
 */
export function plotMonthlySpendings(product, startDate, endDate, elem, isSmall) {
  const monthly = product.monthlyFinancials;
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
      color: 'rgba(45, 52, 138, 0.3)',  // result in #c0c2dc with opacity
      line: {width: 0}  // for ie9 only
    }
  };
  const forecastTrace = {
    x: futureMonths.map(toLabel),
    y: futureTotalCosts.map(round),
    name: 'Forecast spend',
    type: 'bar',
    marker: {
      color: 'rgba(-238, 102, 102, 0.3)',  // result in #add1d1 with opacity
      line: {width: 0}  // for ie9 only
    }
  };
  const layout = {
    // title: 'Monthly expenditure',
    font: {
      family: 'nta, Arial, sans-serif',
      size: isSmall ? 8 : 12
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

  if (isSmall) {
    Object.assign(layout, {autosize: false, width: 640, height: 210});
  };

  const data = [ actualTrace, forecastTrace ];
  return Plotly.newPlot(elem, data, layout, { displayModeBar: false });
}
