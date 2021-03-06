import moment from 'moment';

import Plotly from '../libs/plotly-custom';
import { round, monthRange } from '../libs/utils';

/**
 * work out the shapes and annotations for
 * shapes and annotations representing product
 * phases
 * */
function backgroundForPhases(product, range, isSmall) {
  const phases = product.phases;
  const shapes = [];
  const annotations = [];

  Object.keys(phases).map(name => {
    const {start, end, color} = phases[name];
    if (start) {
      const x1 = end ? end : range[1].format('YYYY-MM-DD');
      shapes.push({
        type: 'rect',
        layer: 'below',
        xref: 'x',
        yref: 'paper',
        x0: start,
        x1: x1,
        y0: 0,
        y1: 1,
        fillcolor: color,
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
        y: isSmall ? -0.3 : -0.2,
        text: `<b>${name.toUpperCase()}</b>`,
        showarrow: false,
        bgcolor: color,
        font: {
          color: '#ffffff',
          size: isSmall ? 8 : 16
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
      width: 2,
      dash: 'dashdot'
    }
  };
  const annotation = {
    yref: 'paper',
    x: x,
    xanchor: 'left',
    y: 1,
    text: 'Today',
    showarrow: true,
    ax: 0,
    ay: -15
  };
  return {shape, annotation}
}


/**
 * line and annotation to indicate end date of the product
 **/
function markingsForEndDate(endDate, range) {
  // plot a line for today if within the time frame
  const endDateMoment = moment(endDate);
  if (endDateMoment < range[0] || endDateMoment > range[1]) {
    return null;
  }
  const x = endDateMoment.add(1, 'days').format('YYYY-MM-DD');
  const shape = {
    type: 'line',
    xref: 'x',
    yref: 'paper',
    x0: x,
    x1: x,
    y0: 0,
    y1: 1,
    line: {
      width: 2,
      color: '#974AB2'
    }
  };
  const annotation = {
    yref: 'paper',
    x: x,
    xanchor: 'left',
    y: 1,
    text: 'End',
    font: {color: '#974AB2'},
    showarrow: true,
    ax: 0,
    ay: -15,
    arrowcolor: '#974AB2'
  };
  return {shape, annotation}
}


export function plotCumulativeSpendings(product, showBurnDown, startDate, endDate, elem, isSmall) {
  const today = moment().format('YYYY-MM-DD');
  const keyDatesFinancials = product.keyDatesFinancials;
  const keyDates = Object.keys(keyDatesFinancials).sort();
  const pastDates = keyDates.filter(d => d <= today).sort();
  const futureDates = keyDates.filter(d => d >= today).sort();
  const finalKeyDate = keyDates.slice(-1)[0];
  const remainingDates = monthRange(finalKeyDate, endDate, 'end');
  const datesExtended = keyDates.concat(remainingDates);

  const actualCumulativeTrace = {
    x: pastDates,
    y: pastDates.map(d => round(keyDatesFinancials[d].total)),
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
    x: pastDates,
    y: pastDates.map(d => round(keyDatesFinancials[d].remaining)),
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
    x: futureDates,
    y: futureDates.map(d => round(keyDatesFinancials[d].total)),
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
  const forecastRemainingTrace = {
    x: datesExtended.filter(d => d >= today),
    y: datesExtended.filter(d => d >= today).map(d => {
      if (d in keyDatesFinancials) {
        return round(keyDatesFinancials[d].remaining)
      };
      return round(keyDatesFinancials[finalKeyDate].remaining);
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

  const budgetTrace = {
    x: datesExtended,
    y: datesExtended.map(d => {
      if (d in keyDatesFinancials) {
        return round(keyDatesFinancials[d].budget);
      };
      return round(keyDatesFinancials[finalKeyDate].budget);
    }),
    name: 'Budget',
    type: 'scatter',
    mode: 'lines+markers',
    yaxis: 'y',
    marker: {
      color: '#274028',
      line: {width: 0}  // for ie9 only
    },
    line: {
      dash: 'dot',
      shape: 'hv'
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
    moment(startDate, 'YYYY-MM-DD'),
    moment(endDate, 'YYYY-MM-DD').add(1, 'day')
  ];

  const {shapes, annotations} = backgroundForPhases(product, range, isSmall);
  const todayMarkings = markingsForToday(range);
  if (todayMarkings) {
    shapes.push(todayMarkings.shape);
    annotations.push(todayMarkings.annotation);
  };
  if (product.endDate) {
    const endDateMarkings = markingsForEndDate(product.endDate, range);
    if (endDateMarkings) {
      shapes.push(endDateMarkings.shape);
      annotations.push(endDateMarkings.annotation);
    }
  };
  const layout = {
    // title: 'Total expenditure and budget',
    font: {
      family: 'nta, Arial, sans-serif',
      size: isSmall ? 8 : 12
    },
    xaxis: {
      type: 'date',
      range: range.map(m => m.valueOf()),
      nticks: 18,
      tickformat: '%-d %b %y',
      hoverformat: '%-d %b %y'
    },
    yaxis: {
      rangemode: 'tozero',
      tickprefix: '\u00a3'
    },
    legend: {
      yanchor: 'top'
    },
    shapes: shapes,
    annotations: annotations,
    margin: {
      t: 20,
      l: 50,
      r: 50
    }
  };
  if (isSmall) {
    Object.assign(layout, {autosize: false, width: 640, height: 210});
  };

  return Plotly.newPlot(elem, data, layout, { displayModeBar: false });
}
