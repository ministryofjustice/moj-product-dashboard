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
         min, max, values, round } from './utils';
import { plotCumulativeSpendings } from './cumulative-graph';

import RedImg from '../img/red.png';
import AmberImg from '../img/amber.png';
import GreenImg from '../img/green.png';

/**
 * send a POST request to the backend to retrieve project profile
 */
export function getProjectData(type, id, startDate, endDate, csrftoken) {
  const urls = {
    project: '/project.json',
    'project-group': '/project-group.json'
  };
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
  return fetch(urls[type], init)
    .then(response => response.json());
}

/**
 * parse the financial infomation about the project
 */
export function parseProjectFinancials(financial) {
  const result = {};
  let cumulative = 0;

  Object.keys(financial).sort().map(month => {
    const mf = financial[month];
    const budget = parseFloat(mf['budget']);
    const total = parseFloat(mf['contractor']) +
                  parseFloat(mf['non-contractor']) +
                  parseFloat(mf['additional']);

    cumulative += total;
    const remaining = budget - cumulative;
    const ms = moment(month, 'YYYY-MM').format('YYYY-MM');
    result[ms] = { total, cumulative, budget, remaining };
  });

  return result;
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
      firstDate: null,
      lastDate: null,
      minStartDate: null,
      maxEndDate: null
    };
  }

  get timeFrames() {
    const now = moment();
    return {
      'entire-time-span': {
        label: 'Entire project life time',
        startDate: this.state.firstDate,
        endDate: this.state.lastDate
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

  getMinStartDate(firstDate) {
    const candidates = values(this.timeFrames)
      .map(tf => tf.startDate)
      .filter(date => date != null);
    candidates.push(startOfMonth(firstDate));
    return min(candidates);
  }

  getMaxEndDate(lastDate) {
    const candidates = values(this.timeFrames)
      .map(tf => tf.endDate)
      .filter(date => date != null);
    candidates.push(startOfMonth(lastDate));
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
    const { startDate, endDate } = this.timeFrames[this.state.timeFrame];
    getProjectData(this.props.type, this.props.id, startDate,
                   endDate, this.props.csrftoken)
      .then(project => {
        const firstDate = project['first_date'];
        const lastDate = project['last_date'];
        this.setState({
          project: project,
          firstDate: startOfMonth(firstDate),
          lastDate: endOfMonth(lastDate),
          minStartDate: this.getMinStartDate(firstDate),
          maxEndDate: this.getMaxEndDate(lastDate),
          startDate: startOfMonth(firstDate),
          endDate: endOfMonth(lastDate),
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
      const { startDate, endDate } = this.timeFrames[nextState.timeFrame];
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
      this.setState({startDate: startDate, endDate: endDate});
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
      <TimeFrameSelector rangeOptions={this.timeFrameOpts}
        selectedRange={this.state.timeFrame}
        onRangeChange={evt => this.handleTimeFrameChange(evt)}
        selectedStartDate={this.state.startDate}
        selectedEndDate={this.state.endDate}
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
        <h1 className="heading-xlarge">{this.state.project.name}</h1>
        <hr />
        <KeyStats
          budget={this.state.project.budget}
          costToDate={this.state.project['cost_to_date']}
          savings={this.state.project.savings}
        />
        <hr/>
        <h3 className="heading-medium">Total expenditure and budget</h3>
        { timeFrameSelector }
        <ProjectGraph
          onChange={(e) => this.handleBurnDownChange(e)}
          project={this.state.project}
          showBurnDown={this.state.showBurnDown}
          startDate={this.state.startDate}
          endDate={this.state.endDate}
        />
      </div>
    );
  }
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


function KeyStats({budget, costToDate, savings}) {

  const Data = ({data, label}) => (
    <div className="column-one-third">
      <div className="data">
        <h2 className="bold-xlarge">{data}</h2>
        <p className="bold-xsmall">{label}</p>
      </div>
    </div>
  );

  const format = (data) => `£${Math.round(parseFloat(data)).toLocaleString()}`;

  return (
    <div>
      <h3 className="heading-medium">Key statistics</h3>
      <div className="grid-row">
        <Data
          data={format(budget)}
          label="Budget"
        />
        <Data
          data={format(costToDate)}
          label="Total spend to date"
        />
        <Data
          data={savings ? format(savings) : '\u00a0'}
          label="Savings enabled"
        />
      </div>
    </div>
  )
}

class ProjectGraph extends Component {

  plot() {
    if (Object.keys(this.props.project).length === 0) {
      return;
    }
    plotCumulativeSpendings(
      this.props.project,
      this.props.showBurnDown,
      this.props.startDate,
      this.props.endDate,
      this.container1
    );
    plotMonthlySpendings(
      this.props.project,
      this.props.startDate,
      this.props.endDate,
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


/**
 * plot the graph for a project's monthly spendings
 */
function plotMonthlySpendings(project, startDate, endDate, elem) {
  const monthly = parseProjectFinancials(project.financial);
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
      'displayName': 'Product',
      'customComponent': (props) => (
        <a href={`/projects/${props.rowData.id}`}>
          {props.data}
        </a>
      ),
    },
    {
      'columnName': 'financial_rag',
      'order': 3,
      'displayName': 'Financial RAG',
      'customComponent': (props) => {
        const mapping = { RED: RedImg, AMBER: AmberImg, GREEN: GreenImg };
        return (
            <img src={ mapping[props.data] } className="rag" alt={props.data} />
          )}
    },
    {
      'columnName': 'current_fte',
      'order': 4,
      'displayName': 'Current FTE',
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
