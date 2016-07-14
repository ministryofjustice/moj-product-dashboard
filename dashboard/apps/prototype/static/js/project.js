import 'whatwg-fetch';
import moment from 'moment';
import Griddle from 'griddle-react';
import React, { Component } from 'react';
import Spinner from 'react-spinkit';
import { Select, Radio, config } from 'rebass';

import Plotly from './plotly-custom';
import { monthRange, thisCalendarYear,
         thisFinancialYear, thisQuarter, lastCalendarYear,
         lastFinancialYear, lastQuarter,
         startOfMonth, endOfMonth,
         min, max, values } from './utils';

/**
 * send a POST request to the backend to retrieve project profile
 */
export function getProjectData(id, startDate, endDate, csrftoken) {
  const init = {
    credentials: 'same-origin',
    method: 'POST',
    headers: {
      'X-CSRFToken': csrftoken,
      'Accept': 'application/json',
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({id: id, startDate: startDate, endDate: endDate})
  };
  return fetch('/project.json', init)
    .then(response => response.json());
}

/**
 * parse the financial infomation about the project
 */
export function parseProjectFinancials(financial, thisMonth) {
  const _months = Object.keys(financial).sort();
  const _pastMonths = _months
    .filter(m => moment(m, 'YYYY-MM') < moment(thisMonth).startOf('month'));
  const _futureMonths = _months
    .filter(m => moment(m, 'YYYY-MM') >= moment(thisMonth).startOf('month'));

  const costs = _months.map(month => financial[month]);
  const budget = costs.map(c => parseFloat(c['budget']));

  const pastCosts = _pastMonths.map(month => financial[month]);
  const pastTotalCosts = pastCosts.map(c =>
     parseFloat(c['contractor']) +
     parseFloat(c['non-contractor']) +
     parseFloat(c['additional']));
  const pastCumulative = [];
  let cumulative = 0;
  pastTotalCosts.map(c => {
    cumulative += c;
    pastCumulative.push(cumulative);
  });
  // TODO: this is wrong to calculate remainings!
  const pastRemainings = pastCumulative
    .map((val, index) => budget[index] - val);

  const futureCosts = _futureMonths.map(month => financial[month]);
  const futureTotalCosts = futureCosts.map(c =>
     parseFloat(c['contractor']) +
     parseFloat(c['non-contractor']) +
     parseFloat(c['additional']));
  const futureCumulative = [];
  futureTotalCosts.map(c => {
    cumulative += c;
    futureCumulative.push(cumulative);
  });
  const futureRemainings = futureCumulative
    .map((val, index) => budget[index + pastCumulative.length] - val)

  const parseMonthLabel = m => moment(m, 'YYYY-MM').format('YYYY-MM')
  const months = _months.map(parseMonthLabel);
  const pastMonths = _pastMonths.map(parseMonthLabel);
  const futureMonths = _futureMonths.map(parseMonthLabel);

  return {
    months,
    budget,
    pastMonths,
    pastTotalCosts,
    pastCumulative,
    pastRemainings,
    futureMonths,
    futureTotalCosts,
    futureCumulative,
    futureRemainings
  };
}


export class ProjectContainer extends Component {

  constructor(props) {
    super(props);
    this.state = {
      showBurnDown: false,
      hasData: false,
      project: {},
      timeFrame: 'entire-time-span',
      startDate: '',
      endDate: '',
      firstSpendingDate: null,
      lastSpendingDate: null,
      minStartDate: null,
      maxEndDate: null
    };
  }

  get timeFrames() {
    const now = moment();
    return {
      'entire-time-span': {
        label: 'Entire project life time',
        startDate: this.state.firstSpendingDate,
        endDate: this.state.lastSpendingDate
      },
      'this-year': {
        label: 'This calendar year',
        startDate: thisCalendarYear(now).startDate,
        endDate: thisCalendarYear(now).endDate
      },
      'this-financial-year': {
        label: 'This financial year',
        startDate: thisFinancialYear(now).startDate,
        endDate: thisFinancialYear(now).endDate
      },
      'this-quarter': {
        label: 'This quarter',
        startDate: thisQuarter(now).startDate,
        endDate: thisQuarter(now).endDate
      },
      'last-year': {
        label: 'Last calendar year',
        startDate: lastCalendarYear(now).startDate,
        endDate: lastCalendarYear(now).endDate
      },
      'last-financial-year': {
        label: 'Last financial year',
        startDate: lastFinancialYear(now).startDate,
        endDate: lastFinancialYear(now).endDate
      },
      'last-quarter': {
        label: 'Last quarter',
        startDate: lastQuarter(now).startDate,
        endDate: lastQuarter(now).endDate
      },
      'custom-range': {
        label: 'Custom date range',
        startDate: null,
        endDate: null
      },
    }
  }

  get timeFrameOpts() {
    return Object.keys(this.timeFrames)
      .map(key => ({
        value: key,
        children: this.timeFrames[key].label
      }))
  }

  getMinStartDate(firstSpendingDate) {
    const candidates = values(this.timeFrames)
      .map(tf => tf.startDate)
      .filter(date => date != null);
    candidates.push(startOfMonth(firstSpendingDate));
    return min(candidates);
  }

  getMaxEndDate(lastSpendingDate) {
    const candidates = values(this.timeFrames)
      .map(tf => tf.endDate)
      .filter(date => date != null);
    candidates.push(startOfMonth(lastSpendingDate));
    return max(candidates);
  }

  matchTimeFrame(startDate, endDate) {
    const matched = Object.keys(this.timeFrames).filter(
        key => {
          const val = this.timeFrames[key];
          return (val.startDate == startDate && val.endDate == endDate);
        });
    if (matched.length > 0) {
      return matched[0];
    }
    return 'custom-range';
  }

  componentDidMount() {
    const timeFrame = this.timeFrames[this.state.timeFrame];
    const startDate = timeFrame.startDate;
    const endDate = timeFrame.endDate;
    getProjectData(this.props.id, startDate, endDate, this.props.csrftoken)
      .then(project => {
        const firstSpendingDate = project['first_spending_date'];
        const lastSpendingDate = project['last_spending_date'];
        this.setState({
          project: project,
          firstSpendingDate: startOfMonth(firstSpendingDate),
          lastSpendingDate: endOfMonth(lastSpendingDate),
          minStartDate: this.getMinStartDate(firstSpendingDate),
          maxEndDate: this.getMaxEndDate(lastSpendingDate),
          startDate: startOfMonth(firstSpendingDate),
          endDate: endOfMonth(lastSpendingDate),
          hasData: true
        });
      });
  }

  handleBurnDownChange(e) {
    this.setState({showBurnDown: e.target.value == 'burn-down'});
  }

  get startDateOpts() {
    return monthRange(this.state.minStartDate, this.state.maxEndDate, 'start')
      .map(m => ({
        value: m,
        children: moment(m).format('MMM YY'),
      }));
  }

  get endDateOpts() {
    return monthRange(this.state.minStartDate, this.state.maxEndDate, 'end')
      .filter(m => moment(m) >= moment(this.state.startDate) || m == this.state.endDate)
      .map(m => ({
        value: m,
        children: moment(m).format('MMM YY')
      }));
  }

  componentWillUpdate(nextProps, nextState) {

    // when timeFrame changes
    if (this.state.timeFrame != nextState.timeFrame) {
      const timeFrame = this.timeFrames[nextState.timeFrame];
      const startDate = timeFrame.startDate;
      const endDate = timeFrame.endDate;
      if (startDate && endDate) {
        this.setState({startDate: startDate, endDate: endDate});
      }
    };

    const startDate = nextState.startDate;
    const endDate = nextState.endDate;
    // when first start
    if (this.state.startDate === '' || this.state.endDate === '') {
      return;
    };
    // when picked up a start date greater than previous end date
    if (startDate > endDate) {
      return;
    };
    // when startDate or endDate changes
    if (this.state.startDate != startDate || this.state.endDate != endDate) {
      this.setState({hasData: false});
      getProjectData(this.props.id, startDate, endDate, this.props.csrftoken)
        .then(project => {
          console.log(project);
          this.setState({project: project, hasData: true});
        });
    };
  }

  handleTimeFrameChange(evt) {
    if (this.state.timeFrame != evt.target.value) {
      this.setState({
        timeFrame: evt.target.value
      });
    }
  }

  handleStartDateChange(evt) {
    const startDate = evt.target.value;
    // do nothing if there is no change
    if (startDate == this.state.startDate) {
      return;
    }
    const endDate = this.state.endDate;
    this.setState({
      startDate: startDate,
      timeFrame: this.matchTimeFrame(startDate, endDate)
    });
  }

  handleEndDateChange(evt) {
    const startDate = this.state.startDate;
    const endDate = evt.target.value;
    // do nothing if there is no change
    if (endDate == this.state.endDate) {
      return;
    }
    this.setState({
      endDate: endDate,
      timeFrame: this.matchTimeFrame(startDate, endDate)
    });
  }

  render() {
    const timeFrameSelector = (
      <TimeFrameSelector
        rangeOptions={this.timeFrameOpts}
        selectedRange={this.state.timeFrame}
        onRangeChange={evt => this.handleTimeFrameChange(evt)}
        selectedStartDate={this.state.startDate}
        selectedEndDate={this.state.endDate}
        minStartDate={this.state.minStartDate}
        startDateOpts={this.startDateOpts}
        endDateOpts={this.endDateOpts}
        onSelectedStartDateChange={evt => this.handleStartDateChange(evt)}
        onSelectedEndDateChange={evt => this.handleEndDateChange(evt)}
      />);

    if (! this.state.hasData) {
      return (
        <div>
          { timeFrameSelector }
          <div className="graph-spinkit">
            <Spinner spinnerName='three-bounce' />
          </div>
        </div>
      );
    };

    return (
      <div>
        { timeFrameSelector }
        <ProjectGraph
          onChange={(e) => this.handleBurnDownChange(e)}
          project={this.state.project}
          showBurnDown={this.state.showBurnDown}
        />
      </div>
    );
  }
}

function getYRange(showBurnDown, remainings, cumulatives, budget) {
  let minY, maxY;
  if (showBurnDown) {
    const minRemaining = min(remainings);
    const maxRemaining = max(remainings);
    minY = minRemaining > 0 ? 0 : minRemaining;
    maxY = maxRemaining < 0 ? 0 : maxRemaining;
  } else {
    minY = 0;
    maxY = max(budget.concat(cumulatives));
  }
  // make it slightly bigger;
  minY = 1.1 * minY;
  maxY = 1.1 * maxY;
  return {minY, maxY};
}


function plotCumulativeSpendings(project, showBurnDown, elem) {
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

  const {minY, maxY} = getYRange(
    showBurnDown,
    pastRemainings.concat(futureRemainings),
    pastCumulative.concat(futureCumulative),
    budget
  );

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

  const layout = Object.assign(
    phaseRects(project, range),
    {
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
      }
    }
  );

  // plot a line for today if within the time frame
  const today = moment().format('YYYY-MM-DD');
  if (today > months[0] && today < endOfMonth(months[ months.length -1 ])) {
    layout['shapes'].push(
      {
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
      }
    );
    layout['annotations'].push({
      yref: 'paper',
      x: today,
      xanchor: 'left',
      y: 0.3,
      text: 'Today',
      showarrow: false
    });
  }


  Plotly.newPlot(elem, data, layout, { displayModeBar: false });
}

function TimeFrameSelector({
  rangeOptions,
  selectedRange,
  onRangeChange,
  startDateOpts,
  selectedStartDate,
  onSelectedStartDateChange,
  endDateOpts,
  selectedEndDate,
  onSelectedEndDateChange}) {

  return (
    <div className="grid-row">
      <div className="column-one-quarter">
        <Select
          name="form-field-name"
          value={selectedRange}
          options={rangeOptions}
          onChange={onRangeChange}
          label="Show data for"
        />
      </div>
      <div className="column-one-quarter">
        <Select
          name="start-date"
          options={startDateOpts}
          value={selectedStartDate}
          onChange={onSelectedStartDateChange}
          label="from"
        />
      </div>
      <div className="column-one-quarter">
        <Select
          name="end-date"
          options={endDateOpts}
          value={selectedEndDate}
          onChange={onSelectedEndDateChange}
          label="to"
        />
      </div>
    </div>
  );
}


class ProjectGraph extends Component {

  plot() {
    if (Object.keys(this.props.project).length === 0) {
      return;
    }
    plotCumulativeSpendings(
      this.props.project,
      this.props.showBurnDown,
      this.container1
    );
    plotMonthlySpendings(
      this.props.project,
      this.container2
    );
  }

  componentDidUpdate() {
    this.plot();
  }

  componentDidMount() {
    this.plot();
  }

  render() {
    return (
      <div>
        <Radio
          checked={!this.props.showBurnDown}
          circle
          label="Show burn up"
          name="burn-up-burn-down"
          value="burn-up"
          onChange={this.props.onChange}
        />
        <Radio
          checked={this.props.showBurnDown}
          circle
          label="Show burn down"
          name="burn-up-burn-down"
          value="burn-down"
          onChange={this.props.onChange}
        />
        <div ref={(elem) => this.container1=elem} />
        <div ref={(elem) => this.container2=elem} />
      </div>
    );
  }
}


function phaseRects(project, xRange) {

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
      end: xRange[1].format('YYYY-MM-DD'),
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
        opacity: 0.2,
        line: {
          width: 0
        }
      });
      annotations.push({
        yref: 'paper',
        x: moment((moment(start) + moment(end)) / 2).format('YYYY-MM-DD'),
        y: -0.2,
        text: phase,
        showarrow: false
      });
    };
  });

  return {shapes, annotations};
}

/**
 * plot the graph for a project's monthly spendings
 */
function plotMonthlySpendings(project, elem) {
  const { pastMonths,
          pastTotalCosts,
          futureMonths,
          futureTotalCosts } = parseProjectFinancials(project.financial);

  // NOTE: those lines for ie9 is related to this issue
  // https://github.com/plotly/plotly.js/issues/166
  const toLabel = m => moment(m, 'YYYY-MM').format('MMM YY');
  const actualTrace = {
    x: pastMonths.map(toLabel),
    y: pastTotalCosts,
    name: 'Actual spend',
    type: 'bar',
    marker: {
      color: '#c0c2dc',
      line: {width: 0}  // for ie9 only
    }
  };
  const forecastTrace = {
    x: futureMonths.map(toLabel),
    y: futureTotalCosts,
    name: 'Forecast spend',
    type: 'bar',
    marker: {
      color: '#add1d1',
      line: {width: 0}  // for ie9 only
    }
  };
  const layout = {
    title: 'Monthly expenditure',
    font: {
      family: 'nta'
    },
    barmode: 'stack',
    yaxis: {
      tickprefix: '\u00a3'
    },
    legend: {
      yanchor: 'bottom'
    }
  };
  const data = [ actualTrace, forecastTrace ];
  Plotly.newPlot(elem, data, layout, { displayModeBar: false });
}


/**
 * React component for a table of projects
 */
export const ProjectsTable = ({ projects, showService, showFilter }) => {

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
      'order': 3,
      'displayName': 'RAG',
    },
    {
      'columnName': 'team_size',
      'order': 4,
      'displayName': 'Team size',
      'customCompareFn': Number,
      'customComponent': (props) => (
        <span>
          {Number(props.data).toFixed(1)}
        </span>),
    },
    {
      'columnName': 'cost_to_date',
      'order': 5,
      'displayName': 'Cost to date',
      'customCompareFn': Number,
      'customComponent': displayMoney,
    },
    {
      'columnName': 'budget',
      'order': 6,
      'displayName': 'Budget',
      'customCompareFn': Number,
      'customComponent': displayMoney,
    }
  ];

  if (showService) {
    columnMetadata.push({
      'columnName': 'service_area',
      'order': 2,
      'displayName': 'Service area',
      'customCompareFn': (serv) => serv.name,
      'customComponent': (props) => (
        <a href={`/services/${props.data.id}`}>
          {props.data.name}
        </a>
      )
    });
  };

  return (
    <Griddle
      results={projects}
      columns={columnMetadata.map(item => item['columnName'])}
      columnMetadata={columnMetadata}
      useGriddleStyles={false}
      bodyHeight={800}
      resultsPerPage={100}
      showFilter={showFilter}
    />
  );
}
