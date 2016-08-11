import Plotly from './plotly-custom';
import moment from 'moment';

import { parseProjectFinancials } from './project';
import { endOfMonth, round, monthRange } from './utils';

/**
 * work out the date labels for the xaxis
 * depending on the length of the time frame.
 * if the duration is less than 11 months
 * show the day month and year otherwise
 * just show the month and year
 **/
function tickFormat(range) {
  const duration = moment.duration(range[1] - range[0]).asMonths();
  if (duration > 11) {
    return '%b %y';
  };
  return '%-d %b %y';
}

/**
 * work out the shapes and annotations for
 * shapes and annotations representing product
 * phases
 * */
function backgroundForPhases(project, range) {
  const discovery = project['discovery_date'];
  const alpha = project['alpha_date'];
  const beta = project['beta_date'];
  const live = project['live_date'];

  const phases = {
    'discovery': {
      start: discovery,
      end: alpha,
      fillcolor: '#972c86'
    },
    'alpha': {
      start: alpha,
      end: beta,
      fillcolor: '#d53880'
    },
    'beta': {
      start: beta,
      end: live,
      fillcolor: '#fd7743'
    },
    'live': {
      start: live,
      fillcolor: '#839951'
    }
  }
  const shapes = [];
  const annotations = [];

  Object.keys(phases).map( phase => {
    const {start, end, fillcolor} = phases[phase];
    if (start) {
      const x1 = end ? end : range[1].format('YYYY-MM-DD');
      shapes.push({
        type: 'rect',
        xref: 'x',
        yref: 'paper',
        x0: start,
        x1: x1,
        y0: 0,
        y1: 1,
        fillcolor: fillcolor,
        opacity: 0.3,
        line: {
          width: 0
        }
      });
      const l = moment(start) > range[0] ? moment(start): range[0];
      const h = moment(x1) < range[1] ? moment(x1) : range[1];
      annotations.push({
        yref: 'paper',
        x: moment((l + h) / 2).format('YYYY-MM-DD'),
        y: -0.2,
        text: phase.toUpperCase(),
        showarrow: false,
        bgcolor: fillcolor,
        font: {
          color: '#ffffff',
          size: 16
        },
        borderpad: 4
      });
    };
  });

  return {shapes, annotations};
}

/**
 * line and annotation to indicate today on the graph
 **/
function markingsForToday(range) {
  // plot a line for today if within the time frame
  const today = moment();
  if (today < range[0] || today > range[1]) {
    return null;
  }
  const x = today.format('YYYY-MM-DD');
  const shape = {
    type: 'line',
    xref: 'x',
    yref: 'paper',
    x0: x,
    x1: x,
    y0: 0,
    y1: 1,
    line: {
      width: 0.3,
      dash: 'dashdot'
    }
  };
  const annotation = {
    yref: 'paper',
    x: x,
    xanchor: 'left',
    y: 0.3,
    text: 'Today',
    showarrow: false
  };
  return {shape, annotation}
}


export function plotCumulativeSpendings(project, showBurnDown, startDate, endDate, elem) {
  const currentMonth = moment().format('YYYY-MM');
  const lastMonth = moment().subtract(1, 'month').format('YYYY-MM');
  const monthly = parseProjectFinancials(project.financial);
  const months = Object.keys(monthly).sort();
  const finalMonth = months.slice(-1)[0];
  const remainingMonths = monthRange(finalMonth, endDate, 'end');
  const monthsExtended = months.concat(remainingMonths);
  const pastMonths = months.filter(m => m < currentMonth);
  const lastPlusFutureMonths = months.filter(m => m >= lastMonth);
  const lastPlusFutureMonthsExtended = lastPlusFutureMonths.concat(remainingMonths);

  const toLabel = m => endOfMonth(moment(m, 'YYYY-MM'));

  const actualCumulativeTrace = {
    x: pastMonths.map(toLabel),
    y: pastMonths.map(m => round(monthly[m].cumulative)),
    name: 'Actual spend',
    type: 'scatter',
    mode: 'lines+markers',
    yaxis: 'y',
    marker: {
      color: '#6F777B',
      line: {width: 0}  // for ie9 only
    }
  };
  const actualRemainingTrace = {
    x: pastMonths.map(toLabel),
    y: pastMonths.map(m => round(monthly[m].remaining)),
    name: 'Actual spend',
    type: 'scatter',
    mode: 'lines+markers',
    yaxis: 'y',
    marker: {
      color: '#B29000',
      line: {width: 0}  // for ie9 only
    }
  };

  const forecastCumulativeTrace = {
    x: lastPlusFutureMonths.map(toLabel),
    y: lastPlusFutureMonths.map(m => round(monthly[m].cumulative)),
    name: 'Forecast spend',
    type: 'scatter',
    mode: 'lines+markers',
    yaxis: 'y',
    line: {
      dash: 'dot'
    },
    marker: {
      color: '#6F777B',
      line: {width: 0}  // for ie9 only
    }
  };
  const finalRemaining = round(monthly[finalMonth].remaining);
  const forecastRemainingTrace = {
    x: lastPlusFutureMonthsExtended.map(toLabel),
    y: lastPlusFutureMonthsExtended.map(m => {
      if (m in monthly) {
        return round(monthly[m].remaining);
      }
      return finalRemaining;
    }),
    name: 'Forecast spend',
    type: 'scatter',
    mode: 'lines+markers',
    yaxis: 'y',
    marker: {
      color: '#B29000',
      line: {width: 0}  // for ie9 only
    },
    line: {
      dash: 'dot'
    }
  };

  const finalBudget = round(monthly[finalMonth].budget);
  const budgetTrace = {
    x: monthsExtended.map(toLabel),
    y: monthsExtended.map(m => {
      if (m in monthly) {
        return round(monthly[m].budget);
      }
      return finalBudget;
    }),
    name: 'Budget',
    type: 'scatter',
    mode: 'lines+markers',
    yaxis: 'y',
    marker: {
      color: '#FFBF47',
      line: {width: 0}  // for ie9 only
    },
    line: {
      dash: 'dot'
    }
  };

  const data = [];

  if (showBurnDown) {
    data.push(actualRemainingTrace);
    data.push(forecastRemainingTrace);
  } else {
    data.push(actualCumulativeTrace);
    data.push(forecastCumulativeTrace);
    data.push(budgetTrace);
  };

  const range =  [ moment(startDate, 'YYYY-MM-DD'), moment(endDate, 'YYYY-MM-DD') ];

  const {shapes, annotations} = backgroundForPhases(project, range);
  const todayMarkings = markingsForToday(range);
  if (todayMarkings) {
    shapes.push(todayMarkings.shape);
    annotations.push(todayMarkings.annotation);
  }
  const layout = {
    title: 'Total expenditure and budget',
    font: {
      family: 'nta'
    },
    xaxis: {
      type: 'date',
      range: range.map(m => m.valueOf()),
      nticks: 18,
      tickformat: tickFormat(range),
      hoverformat: '%-d %b %y'
    },
    yaxis: {
      rangemode: 'tozero',
      tickprefix: '\u00a3'
    },
    legend: {
      yanchor: 'bottom'
    },
    shapes: shapes,
    annotations: annotations
  };

  Plotly.newPlot(elem, data, layout, { displayModeBar: false });
}
