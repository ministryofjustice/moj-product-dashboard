import Plotly from './plotly-custom';
import moment from 'moment';

import { parseProjectFinancials } from './project';
import { startOfMonth, endOfMonth } from './utils';

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
      fillcolor: '#de397f'
    },
    'beta': {
      start: beta,
      end: live,
      fillcolor: '#fd7743'
    },
    'live': {
      start: live,
      end: range[1].format('YYYY-MM-DD'),
      fillcolor: '#839951'
    }
  }
  const shapes = [];
  const annotations = [];

  Object.keys(phases).map( phase => {
    const {start, end, fillcolor} = phases[phase];
    if (start && end) {
      shapes.push({
        type: 'rect',
        xref: 'x',
        yref: 'paper',
        x0: start,
        x1: end,
        y0: 0,
        y1: 1,
        fillcolor: fillcolor,
        opacity: 0.3,
        line: {
          width: 0
        }
      });
      const l = moment(start) > range[0] ? moment(start ): range[0];
      const h = moment(end) < range[1] ? moment(end) : range[1];
      annotations.push({
        yref: 'paper',
        x: moment((l + h) / 2).format('YYYY-MM-DD'),
        y: -0.2,
        text: phase,
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
  const pastMonths = months.filter(m => m < currentMonth);
  const lastPlusFutureMonths = months.filter(m => m >= lastMonth);

  const toLabel = m => endOfMonth(moment(m, 'YYYY-MM'));

  const actualCumulativeTrace = {
    x: pastMonths.map(toLabel),
    y: pastMonths.map(m => monthly[m].cumulative),
    name: 'Actual spend',
    type: 'scatter',
    yaxis: 'y',
    marker: {
      color: '#6F777B',
      line: {width: 0}  // for ie9 only
    }
  };
  const actualRemainingTrace = {
    x: pastMonths.map(toLabel),
    y: pastMonths.map(m => monthly[m].remaining),
    name: 'Actual spend',
    type: 'scatter',
    yaxis: 'y',
    marker: {
      color: '#B29000',
      line: {width: 0}  // for ie9 only
    }
  };

  const forecastCumulativeTrace = {
    x: lastPlusFutureMonths.map(toLabel),
    y: lastPlusFutureMonths.map(m => monthly[m].cumulative),
    name: 'Forecast spend',
    type: 'scatter',
    yaxis: 'y',
    line: {
      dash: 'dot'
    },
    marker: {
      color: '#6F777B',
      line: {width: 0}  // for ie9 only
    }
  };
  const forecastRemainingTrace = {
    x: lastPlusFutureMonths.map(toLabel),
    y: lastPlusFutureMonths.map(m => monthly[m].remaining),
    name: 'Forecast spend',
    type: 'scatter',
    yaxis: 'y',
    marker: {
      color: '#B29000',
      line: {width: 0}  // for ie9 only
    },
    line: {
      dash: 'dot'
    }
  };

  const budgetTrace = {
    x: months.map(toLabel),
    y: months.map(m => monthly[m].budget),
    name: 'Budget',
    type: 'scatter',
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

  const range =  [ moment(startDate), moment(endDate) ];

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
