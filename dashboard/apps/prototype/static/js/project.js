import 'whatwg-fetch';
import moment from 'moment';
import Griddle from 'griddle-react';
import React, { Component } from 'react';
import Spinner from 'react-spinkit';
import Select from 'react-select-plus';

import Plotly from './plotly-custom';
import { monthRange, stripOffDay, thisCalendarYear,
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
  const remainings = budget
    .map((val, index) => val - totalCostsCumulative[index]);
  return {
    months,
    budget,
    civilServantCosts,
    contractorCosts,
    staffCosts,
    additionalCosts,
    totalCostsCumulative,
    remainings
  };
}


export class ProjectContainer extends Component {

  constructor(props) {
    super(props);
    this.state = {
      showRemainings: false,
      hasData: false,
      project: {},
      timeFrame: 'entire-time-span',
      startDate: null,
      endDate: null,
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
        label: this.timeFrames[key].label
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

  handleToggle() {
    this.setState({showRemainings: !this.state.showRemainings});
  }

  get startDateOpts() {
    return monthRange(this.state.minStartDate, this.state.maxEndDate, 'start')
      .map(m => ({
        value: m,
        label: moment(m).format('MMM YY')
      }));
  }

  get endDateOpts() {
    return monthRange(this.state.minStartDate, this.state.maxEndDate, 'end')
      .filter(m => moment(m) >= moment(this.state.startDate))
      .map(m => ({
        value: m,
        label: moment(m).format('MMM YY')
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
    if (this.state.startDate === null || this.state.endDate === null) {
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
          this.setState({project: project, hasData: true});
        });
    };
  }

  handleTimeFrameChange(selection) {
    if (selection && this.state.timeFrame != selection.value) {
      this.setState({
        timeFrame: selection.value
      });
    }
  }

  handleStartDateChange(selection) {
    const startDate = selection.value;
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

  handleEndDateChange(selection) {
    const startDate = this.state.startDate;
    const endDate = selection.value;
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
        onRangeChange={selection => this.handleTimeFrameChange(selection)}
        selectedStartDate={this.state.startDate}
        selectedEndDate={this.state.endDate}
        minStartDate={this.state.minStartDate}
        startDateOpts={this.startDateOpts}
        endDateOpts={this.endDateOpts}
        onSelectedStartDateChange={sel => this.handleStartDateChange(sel)}
        onSelectedEndDateChange={sel => this.handleEndDateChange(sel)}
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
        <label className="form-checkbox">
          <input
            id="show-remainings"
            name="show-remaings"
            type="checkbox"
            onChange={() => this.handleToggle()}
            checked={this.state.showRemainings} />
          Show remaining budget
        </label>
        <ProjectGraph
          project={this.state.project}
          showRemainings={this.state.showRemainings}
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
      <div className="column-one-half">
        <div className="column-one-third">
          <label>Show data for</label>
        </div>
        <div className="column-two-thirds">
          <Select
            placeholder="Select time frame"
            name="form-field-name"
            value={selectedRange}
            options={rangeOptions}
            onChange={onRangeChange}
          />
        </div>
      </div>
      <div className="column-one-quarter">
        <div className="column-one-quarter">from</div>
        <div className="column-three-quarters">
          <Select
            placeholder="Start date"
            options={startDateOpts}
            value={selectedStartDate}
            onChange={onSelectedStartDateChange}
          />
        </div>
      </div>
      <div className="column-one-quarter">
        <div className="column-one-quarter">to</div>
        <div className="column-three-quarters">
          <Select
            placeholder="End date"
            options={endDateOpts}
            value={selectedEndDate}
            onChange={onSelectedEndDateChange}
            className={"top-most"}
          />
        </div>
      </div>
    </div>
  );
}


class ProjectGraph extends Component {

  plot() {
    if (Object.keys(this.props.project).length === 0) {
      return;
    }
    plotProject(
      this.props.project,
      this.props.showRemainings,
      this.container
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
      <div ref={(elem) => this.container=elem} />
    );
  }
}


/**
 * plot the graphs for a project
 */
export function plotProject(project, showRemainings, elem) {
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
    name: 'Budget allocated',
    mode: 'lines',
    yaxis: 'y2',
    marker: {
      color: '#FFBF47',
      line: {width: 0}  // for ie9 only
    }
  };
  const remainingTrace = {
    x: months,
    y: financial.remainings,
    name: 'Budget remaining',
    mode: 'lines',
    yaxis: 'y2',
    marker: {
      color: '#B29000',
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
  ];
  if (showRemainings) {
    data.push(remainingTrace);
  } else {
    data.push(totalCostTrace);
    data.push(budgetTrace);
  };
  Plotly.newPlot(elem, data, layout);
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
