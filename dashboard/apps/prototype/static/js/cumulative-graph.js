import Plotly from './plotly-custom';
import moment from 'moment';

import { parseProjectFinancials } from './project';
import { startOfMonth, endOfMonth } from './utils';

/**
 * work out the shapes and annotations for
 * shapes and annotations representing product
 * phases
 * */
function backgroundForPhases(project, xRange) {

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
      end: xRange[1],
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
      const l = start > xRange[0] ? start : xRange[0];
      const h = end < xRange[1] ? end : xRange[1];
      annotations.push({
        yref: 'paper',
        x: moment((moment(l) + moment(h)) / 2).format('YYYY-MM-DD'),
        y: -0.2,
        text: phase,
        showarrow: false,
        bgcolor: fillcolor,
        font: {
          color: '#ffffff',
          size: 16
        },
        borderpad: 6
      });
    };
  });

  return {shapes, annotations};
}

/**
 * line and annotation to indicate today on the graph
 **/
function markingsForToday(xRange) {
  // plot a line for today if within the time frame
  const today = moment().format('YYYY-MM-DD');
  if (today < xRange[0] || today > xRange[1]) {
    return null;
  }
  const shape = {
    type: 'line',
    xref: 'x',
    yref: 'paper',
    x0: today,
    x1: today,
    y0: 0,
    y1: 1,
    line: {
      width: 0.3,
      dash: 'dashdot'
    }
  };
  const annotation = {
    yref: 'paper',
    x: today,
    xanchor: 'left',
    y: 0.3,
    text: 'Today',
    showarrow: false
  };
  return {shape, annotation}
}


export function plotCumulativeSpendings(project, showBurnDown, elem) {
  const { months,
          budget,
          pastMonths,
          pastCumulative,
          pastRemainings,
          futureMonths,
          futureCumulative,
          futureRemainings } = parseProjectFinancials(project.financial);

  // use current month + future months to ensure continuity
  const index = pastMonths.length -1;
  const currentPlusFutureMonths = [ pastMonths[ index ] ]
    .concat(futureMonths);
  const currentPlusFutureCumulative = [ pastCumulative[ index ] ]
    .concat(futureCumulative);
  const currentPlusFutureRemainings = [ pastRemainings[ index ] ]
    .concat(futureRemainings);

  const toLabel = m => endOfMonth(moment(m, 'YYYY-MM'));

  const actualCumulativeTrace = {
    x: months.map(toLabel),
    y: pastCumulative,
    name: 'Actual spend',
    type: 'scatter',
    yaxis: 'y',
    marker: {
      color: '#6F777B',
      line: {width: 0}  // for ie9 only
    }
  };
  const actualRemainingTrace = {
    x: months.map(toLabel),
    y: pastRemainings,
    name: 'Actual spend',
    type: 'scatter',
    yaxis: 'y',
    marker: {
      color: '#B29000',
      line: {width: 0}  // for ie9 only
    }
  };

  const forecastCumulativeTrace = {
    x: currentPlusFutureMonths.map(toLabel),
    y: currentPlusFutureCumulative,
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
    x: currentPlusFutureMonths.map(toLabel),
    y: currentPlusFutureRemainings,
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
    y: budget,
    name: 'Budget',
    type: 'scatter',
    yaxis: 'y',
    marker: {
      color: '#FFBF47',
      line: {width: 0}  // for ie9 only
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

  const range =  [
    moment(startOfMonth(months[ 0 ])),
    moment(months.slice(-1)[0]).endOf('month')
  ];

  const tickformat = moment.duration(range[1] - range[0]).asMonths() > 11 ? '%b %y' : '%-d %b %y';

  const xRange = range.map(m => m.format('YYYY-MM-DD'));
  const {shapes, annotations} = backgroundForPhases(project, xRange);
  const todayMarkings = markingsForToday(xRange);
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
      tickformat: tickformat,
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
