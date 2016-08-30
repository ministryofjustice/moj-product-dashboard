import 'whatwg-fetch';
import moment from 'moment';
import Griddle from 'griddle-react';
import React, { Component } from 'react';
import Spinner from 'react-spinkit';
import { Select } from 'rebass';
import { Tab, Tabs, TabList, TabPanel } from 'react-tabs';

import Plotly from './plotly-custom';
import { monthRange, thisCalendarYear,
         thisFinancialYear, thisQuarter, lastCalendarYear,
         lastFinancialYear, lastQuarter,
         startOfMonth, endOfMonth, oneDayBefore,
         min, max, values, round, numberWithCommas } from './utils';
import { plotCumulativeSpendings } from './cumulative-graph';

import RedImg from '../img/red.png';
import AmberImg from '../img/amber.png';
import GreenImg from '../img/green.png';
import SeparatorImg from '../img/separator.png';

const statusMapping = {
  'OK': 'status-green',
  'At risk': 'status-amber',
  'In trouble': 'status-red'
};

/**
 * send a POST request to the backend to retrieve project profile
 */
export function getProjectData(type, id, startDate, endDate, csrftoken) {
  const urls = {
    'project': '/project.json',
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
  let spendCumulative = 0;
  let savingsCumulative = 0;

  Object.keys(financial).sort().map(month => {
    const mf = financial[month];
    const budget = parseFloat(mf['budget']);
    const total = parseFloat(mf['contractor']) +
                  parseFloat(mf['non-contractor']) +
                  parseFloat(mf['additional']);
    const savings = parseFloat(mf['savings']);

    spendCumulative += total;
    savingsCumulative += savings;
    const remaining = budget - spendCumulative;
    const ms = moment(month, 'YYYY-MM').format('YYYY-MM');
    result[ms] = { total, spendCumulative, budget, remaining, savings, savingsCumulative };
  });

  return result;
}


export class ProjectContainer extends Component {

  constructor(props) {
    super(props);
    this.state = {
      showBurnDown: false,
      hasData: false,
      project: new Project({}),
      timeFrame: 'entire-time-span',
      startDate: null,
      endDate: null,
    };
    Tabs.setUseDefaultStyles(false);
  }

  get timeFrames() {
    const now = moment();
    const result = {
      'entire-time-span': {
        label: 'Entire project life time',
        startDate: this.state.project.startDate,
        endDate: this.state.project.endDate
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
      }
    };
    const phases = this.state.project.phases;
    Object.keys(phases).map(id => {
      const {start, end, name} = phases[id];
      const formatDate = (date) => moment(date).format('D MMM YY');
      if (start && end ) {
        result[id] = {
          label: `${name} (${formatDate(start)} - ${formatDate(end)})`,
          startDate: startOfMonth(start),
          endDate: endOfMonth(oneDayBefore(end))
        }
      }
    });
    result['custom-range'] = {
      label: 'Custom date range',
      startDate: null,
      endDate: null
    };
    return result;
  }

  get timeFrameOpts() {
    return Object.keys(this.timeFrames)
      .map(key => ({
        value: key,
        children: this.timeFrames[key].label
      }))
  }

  get minStartDate() {
    const candidates = values(this.timeFrames)
      .map(tf => tf.startDate)
      .filter(date => date != null);
    candidates.push(startOfMonth(this.state.startDate));
    return min(candidates);
  }

  get maxEndDate() {
    const candidates = values(this.timeFrames)
      .map(tf => tf.endDate)
      .filter(date => date != null);
    candidates.push(startOfMonth(this.state.endDate));
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
      .then(projectJSON => {
        const project = new Project(projectJSON);
        this.setState({
          project: project,
          startDate: project.startDate,
          endDate: project.endDate,
          hasData: true
        });
      });
  }

  handleBurnDownChange(e) {
    this.setState({showBurnDown: e.target.value == 'burn-down'});
  }


  get startDateOpts() {
    return monthRange(this.minStartDate, this.maxEndDate, 'start')
      .map(m => ({
        value: m,
        children: moment(m).format('MMM YY'),
      }));
  }

  get endDateOpts() {
    return monthRange(this.minStartDate, this.maxEndDate, 'end')
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
    const project = this.state.project;
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

    if (typeof project.name === 'undefined') {
      return (
        <div>
          { timeFrameSelector }
          <div className="graph-spinkit">
            <Spinner spinnerName='three-bounce' />
          </div>
        </div>
      );
    };
    const adminUrl = `/admin/prototype/${project.type}/${project.id}/change/`.toLowerCase();
    return (
      <div>
        <div className="breadcrumbs">
          <ol>
            <li>
              <a href="/">Portfolio Summary</a>
            </li>
            <li style={{ backgroundImage: `url(${SeparatorImg})` }}>
              { project.name }
            </li>
          </ol>
        </div>
        <h1 className="heading-xlarge">
          <div className="banner">
            <PhaseTag phase={ project.phase } />
            <RagTag rag={ project.rag } />
          </div>
          {project.name}
          <a className="button" href={ adminUrl }>
            Edit product details
          </a>
        </h1>
        <Tabs className="product-tabs">
          <TabList>
            <Tab>Overview</Tab>
            <Tab>Product information</Tab>
          </TabList>
          <TabPanel>
            { timeFrameSelector }
            <KeyStats
              startDate={ this.state.startDate }
              endDate={ this.state.endDate }
              project={ project }
              timeFrame={ this.state.timeFrame }
            />
            <ProjectGraph
              project={ project }
              onBurnDownChange={ (e) => this.handleBurnDownChange(e) }
              showBurnDown={ this.state.showBurnDown }
              startDate={ this.state.startDate }
              endDate={ this.state.endDate }
            />
          </TabPanel>
          <TabPanel>
            <ProjectDetails project={ project } />
          </TabPanel>
        </Tabs>
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
          value={selectedStartDate || ''}
          onChange={onSelectedStartDateChange}
          label="From beginning of"
        />
      </div>
      <div className="column-one-quarter">
        <Select
          name="end-date"
          options={endDateOpts}
          value={selectedEndDate || ''}
          onChange={onSelectedEndDateChange}
          label="To end of"
        />
      </div>
    </div>
  );
}


function KeyStats({project, timeFrame, startDate, endDate}) {
  let budget = 0;
  let spend= 0;
  let savings = 0;
  let phaseName = null
  if (timeFrame in project.phases) {
    const { name, start, end }= project.phases[timeFrame];
    phaseName = name;
    const startFinancials = project.keyDatesFinancials[start];
    const endFinancials = project.keyDatesFinancials[end];
    budget = endFinancials.budget;
    spend = endFinancials.total - startFinancials.total;
    savings = endFinancials.savings - startFinancials.savings;
  } else {
    const monthly = project.monthlyFinancials;
    const months = Object.keys(monthly).sort();
    if (months.length > 0) {
      const startMonth = moment(startDate, 'YYYY-MM-DD').format('YYYY-MM');
      const firstMonth = months[0];
      const minMonth = startMonth > firstMonth ? startMonth : firstMonth;
      const endMonth = moment(endDate, 'YYYY-MM-DD').format('YYYY-MM');
      const finalMonth = months.slice(-1)[0];
      const maxMonth = endMonth > finalMonth ? finalMonth : endMonth;

      budget = monthly[maxMonth].budget;
      spend = monthly[maxMonth].spendCumulative
        - monthly[minMonth].spendCumulative
        + monthly[minMonth].total;
      savings = monthly[maxMonth].savingsCumulative
        - monthly[minMonth].savingsCumulative
        + monthly[minMonth].savings;
    }
  }

  const budgetLabel = (endDate, phaseName) => {
    // when there is no data
    if (endDate === null) {
      return 'Budget';
    }
    if (phaseName !== null) {
      return `Budget as of end ${phaseName}`;
    }
    return `Budget as of end ${moment(endDate, 'YYYY-MM-DD').format('MMM YY')}`;
  }
  const format = (data) => `£${numberWithCommas(Math.round(parseFloat(data)))}`;

  const Data = ({data, label}) => (
    <div className="column-one-third">
      <hr/>
      <div className="data">
        <h2 className="bold-xlarge">{data}</h2>
        <p className="bold-xsmall">{label}</p>
      </div>
    </div>
  );

  return (
    <div>
      <h4 className="heading-small">Key statistics</h4>
      <div className="grid-row">
        <Data
          data={format(budget)}
          label={budgetLabel(endDate, phaseName)}
        />
        <Data
          data={format(spend)}
          label={phaseName ? `Spend for ${phaseName}` : "Spend for this period"}
        />
        <Data
          data={format(savings)}
          label={phaseName ? `Savings enabled for ${phaseName}` : "Savings enabled for this period"}
        />
      </div>
    </div>
  )
}

class ProjectGraph extends Component {

  plot() {
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
        <h4 className="heading-small">Total expenditure and budget</h4>
        <hr/>
        <span>Show</span>
        <fieldset className="inline burn-down-toggle">
          <label className="block-label" htmlFor="radio-burn-up">
            <input
              id="radio-burn-up"
              type="radio"
              value="burn-up"
              checked={!this.props.showBurnDown}
              onChange={this.props.onBurnDownChange}
            />
            Burn up
          </label>
          <label className="block-label" htmlFor="radio-burn-down">
            <input
              id="radio-burn-down"
              type="radio"
              value="burn-down"
              checked={this.props.showBurnDown}
              onChange={this.props.onBurnDownChange}
            />
            Burn down
          </label>
        </fieldset>
        <div ref={(elem) => this.container1=elem} />
        <h4 className="heading-small">Monthly expenditure</h4>
        <hr/>
        <div ref={(elem) => this.container2=elem} />
      </div>
    );
  }
}


/**
 * plot the graph for a project's monthly spendings
 */
function plotMonthlySpendings(project, startDate, endDate, elem) {
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
    const number = numberWithCommas(Number(props.data).toFixed(0));
    return (<span>£{number}</span>);
  };

  const columnMetadata = [
    {
      'columnName': 'name',
      'order': 1,
      'displayName': 'Product',
      'customComponent': (props) => {
        let url;
        if (props.rowData.type == 'ProjectGroup') {
          url = `/project-groups/${props.rowData.id}`;
        } else {
          url = `/projects/${props.rowData.id}`;
        };
        return (<a href={url}>{props.data}</a>);
      },
    },
    {
      'columnName': 'phase',
      'order': 3,
      'displayName': 'Phase',
      'customComponent': (props) => {
        const val = props.data === 'Not Defined' ? '' : props.data;
        return (<span>{val}</span>);
      },
      'customCompareFn': (phase) => {
        const val = {Discovery: 0, Alpha: 1, Beta: 2, Live: 3, Ended: 4}[phase];
        return typeof val === 'undefined' ? 5 : val;
      },
    },
    {
      'columnName': 'status',
      'order': 4,
      'displayName': 'Status',
      'customComponent': (props) => {
        if (props.data in statusMapping) {
          return (
            <strong className={statusMapping[props.data]}>{props.data}</strong>
          );
        };
        return null;
      }
    },
    {
      'columnName': 'current_fte',
      'order': 5,
      'displayName': 'Current FTE',
      'customCompareFn': Number,
      'customComponent': (props) => (
        <span>
          {Number(props.data).toFixed(1)}
        </span>),
    },
    {
      'columnName': 'cost_to_date',
      'order': 6,
      'displayName': 'Cost to date',
      'customCompareFn': Number,
      'customComponent': displayMoney,
      'cssClassName': 'money-value'
    },
    {
      'columnName': 'budget',
      'order': 7,
      'displayName': 'Budget',
      'customCompareFn': Number,
      'customComponent': displayMoney,
      'cssClassName': 'money-value'
    },
    {
      'columnName': 'financial_rag',
      'order': 8,
      'displayName': 'Financial RAG',
      'customCompareFn': (label) => {
        const mappings = {RED: 3, AMBER: 2, GREEN: 1};
        return mappings[label];
      },
      'customComponent': (props) => {
        const mapping = { RED: RedImg, AMBER: AmberImg, GREEN: GreenImg };
        return (
            <img src={ mapping[props.data] } className="rag" alt={props.data} />
          )}
    },
    {
      'columnName': 'end_date',
      'order': 9,
      'displayName': 'Estimated end date',
      'customComponent': (props) => {
        const date = moment(props.data, 'YYYY-MM-DD').format('DD/MM/YYYY');
        const val = date === 'Invalid date' ? '' : date;
        return (<span>{val}</span>);
      }
    }
  ];

  if (showService) {
    columnMetadata.push({
      'columnName': 'service_area',
      'order': 2,
      'displayName': 'Service area',
      'customCompareFn': (serv) => serv.name,
      'customComponent': (props) => (
        <span>{props.data.name}</span>
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
      filterPlaceholderText=''
    />
  );
}

function PhaseTag({phase}) {
  const classNameMapping = {
    Discovery: 'phase-tag-discovery',
    Alpha: 'phase-tag-alpha',
    Beta: 'phase-tag-beta',
    Live: 'phase-tag-live',
    Ended: 'phase-tag-ended'
  };
  const className = classNameMapping[phase];
  if (className) {
    return (
      <strong className={`phase-tag ${className}`}>
        { phase }
      </strong>
    );
  };
  return null;
}


function RagTag({rag}) {
  const classNameMapping = {
    RED: 'rag-tag-red',
    AMBER: 'rag-tag-amber',
    GREEN: 'rag-tag-green'
  };
  const className = classNameMapping[rag];
  if (className) {
    return (
      <strong className={`rag-tag ${className}`}>
        RAG
      </strong>
    );
  };
  return null;
}


class Project {
  constructor(projectJSON) {
    this.data = projectJSON;
  }

  get type() {
    return this.data.type;
  }

  get id() {
    return this.data.id;
  }

  get name() {
    return this.data.name;
  }

  get description() {
    return this.data.description;
  }

  get phase() {
    return this.data.phase;
  }

  get rag() {
    return this.data['financial_rag'];
  }

  get status() {
    return this.data.status;
  }

  get startDate() {
    const firstDate = this.data['first_date'];
    return firstDate ? startOfMonth(firstDate) : null;
  }

  get endDate() {
    const lastDate = this.data['last_date'];
    return lastDate? endOfMonth(lastDate) : null;
  }

  get discoveryStart() {
    return this.data['discovery_date'];
  }

  get alphaStart() {
    return this.data['alpha_date'];
  }

  get betaStart() {
    return this.data['beta_date'];
  }

  get liveStart() {
    return this.data['live_date'];
  }

  get serviceArea() {
    return this.data['service_area'].name;
  }

  get productManager() {
    return this.data.managers['product_manager'];
  }

  get deliveryManager() {
    return this.data.managers['delivery_manager'];
  }

  get serviceManager() {
    return this.data.managers['service_manager'];
  }

  get monthlyFinancials() {
    return parseProjectFinancials(this.data.financial['time_frames']);
  }

  get keyDatesFinancials() {
    const result = {};
    values(this.data.financial['key_dates'])
      .map(val => result[val.date] = val.stats);
    return result;
  }

  get phases() {
    return {
      'discovery': {
        start: this.discoveryStart,
        end: this.alphaStart,
        name: 'Discovery',
        color: '#972c86'
      },
      'alpha': {
        start: this.alphaStart,
        end: this.betaStart,
        name: 'Alpha',
        color: '#d53880'
      },
      'beta': {
        start: this.betaStart,
        end: this.liveStart,
        name: 'Beta',
        color: '#fd7743'
      },
      'live': {
        start: this.liveStart,
        name: 'Live',
        color: '#839951'
      }
    }
  };

  get oneOffCosts() {
    return values(this.data.costs).filter(cost => cost.freq == 'One off');
  };

  get recurringCosts() {
    return values(this.data.costs)
      .filter(cost => cost.freq == 'Monthly' || cost.freq == 'Annually');
  };

  get oneOffSavings() {
    return values(this.data.savings).filter(cost => cost.freq == 'One off');
  };

  get recurringSavings() {
    return values(this.data.savings)
      .filter(cost => cost.freq == 'Monthly' || cost.freq == 'Annually');
  };

  get budgets() {
    const returned = values(this.data.financial['key_dates'])
      .filter(data => data.type == 'new budget set')
      .map(data => ({
        name: data.name,
        date: data.date,
        budget: data.stats.budget
      }));
    return returned;
  }

  static compareDate(key, order) {
    return function(obj1, obj2) {
      const v1 = obj1[key];
      const v2 = obj2[key];
      if (v1 > v2) {
        return order == 'desc' ? -1 : 1;
      };
      if (v1 < v2) {
        return order == 'desc' ? 1 : -1;
      };
      return 0;
    }
  };
}

class ProjectDetails extends Component {

  dateInEnglish(date) {
    return moment(date, 'YYYY-MM-DD').format('Do MMM YYYY');
  }

  dateInNum(date) {
    if (date === null) {
      return '-';
    }
    return moment(date, 'YYYY-MM-DD').format('DD/MM/YYYY');
  }

  Status() {
    const status = this.props.project.status;
    let className = 'bold-xlarge';
    if (status in statusMapping) {
      className = `${className} ${statusMapping[status]}`;
    }
    return (
      <div>
        <span className={ className }>{ status || '-' }</span>
        <p className="bold-medium">Product status</p>
      </div>
    );
  }

  PhaseDates() {
    const { discoveryStart, alphaStart,
            betaStart, liveStart, endDate } = this.props.project;
    return (
      <div>
        <div className="grid-row">
          <div className="column-one-quarter">
            <p className="heading-small">Discovery started</p>
            <p>{ discoveryStart ? this.dateInEnglish(discoveryStart) : '-' }</p>
          </div>
          <div className="column-one-quarter">
            <p className="heading-small">Alpha started</p>
            <p>{ alphaStart ? this.dateInEnglish(alphaStart) : '-' }</p>
          </div>
          <div className="column-one-quarter">
            <p className="heading-small">Beta started</p>
            <p>{ betaStart ? this.dateInEnglish(betaStart) : '-' }</p>
          </div>
          <div className="column-one-quarter">
            <p className="heading-small">Live started</p>
            <p>{ liveStart? this.dateInEnglish(liveStart) : '-' }</p>
          </div>
        </div>
        <div className="grid-row">
          <div className="column-one-quarter">
            <p className="heading-small">Estimated end date</p>
            <p>{ endDate ? this.dateInEnglish(endDate) : '-' }</p>
          </div>
        </div>
      </div>
    );
  }

  Recurring(costs) {
    const sortedCosts = costs.sort(Project.compareDate('start_date', 'desc'));

    const Amount = () => {
      if (sortedCosts.length == 0) {
        return (<p>-</p>);
      };
      return (
        sortedCosts.map(cost => {
          const unit = {'Monthly' : 'month', 'Annually': 'year'}[cost.freq];
          const label = `${cost.name} \u00a3${numberWithCommas(cost.cost | 0)}/${unit}`;
          return (<li key={cost.id}>{ label }</li>);
        })
      );
    };

    const Dates = (key) => {
      if (sortedCosts.length == 0) {
        return (<p>-</p>);
      };
      return (
        sortedCosts.map(cost => (
          <li key={cost.id}>{ this.dateInNum(cost[key]) }</li>)
        )
      );
    };

    return (
      <div className="grid-row">
        <div className="column-one-quarter">
          <ul>
            <li className="heading-small">Recurring</li>
            { Amount() }
          </ul>
        </div>
        <div className="column-one-quarter">
          <ul>
            <li className="heading-small">Start date</li>
            { Dates('start_date') }
          </ul>
        </div>
        <div className="column-one-quarter">
          <ul>
            <li className="heading-small">End date</li>
            { Dates('end_date') }
          </ul>
        </div>
      </div>
    );
  }

  OneOff(costs) {
    const sortedCosts = costs.sort(Project.compareDate('start_date', 'desc'));

    const Amount = () => {
      if (sortedCosts.length == 0) {
        return (<p>-</p>);
      };
      return (
        sortedCosts.map(cost => (
          <li key={cost.id}>{ `${cost.name} \u00a3${numberWithCommas(cost.cost | 0)}` }</li>)
        )
      );
    };

    const Dates = () => {
      if (sortedCosts.length == 0) {
        return (<p>-</p>);
      };
      return (
        sortedCosts.map(cost => (
          <li key={cost.id}>{ this.dateInNum(cost['start_date']) }</li>)
        )
      );
    };

    return (
      <div className="grid-row">
        <div className="column-one-quarter">
          <ul>
            <li className="heading-small">One off</li>
            { Amount() }
          </ul>
        </div>
        <div className="column-one-quarter">
          <p className="heading-small"></p>
        </div>
        <div className="column-one-quarter">
          <ul>
            <li className="heading-small">Date</li>
            { Dates() }
          </ul>
        </div>
      </div>
    );
  }

  Budgets() {
    const budgets = this.props.project.budgets
      .sort(Project.compareDate('date', 'desc'));
    if (budgets.length == 0) {
      return (<p>-</p>);
    }
    return (
      <ul style={{marginTop: '20px'}}>
      {
        budgets.map(budget => (
          <li key={budget.date}>
            <span className="heading-small">
              { `Set on ${ this.dateInEnglish(budget.date) }` }
            </span>
            <br/>
            <span>
              {`\u00a3${numberWithCommas(budget.budget | 0)}`}
            </span>
          </li>
          )
        )
      }
      </ul>
    );
  }

  Team() {
    const { serviceManager, productManager, deliveryManager, serviceArea } = this.props.project;
    return (
      <div className="grid-row">
        <div className="column-one-quarter">
            <p className="heading-small">Service manager</p>
            <p>{ serviceManager || '-' }</p>
        </div>
        <div className="column-one-quarter">
            <p className="heading-small">Product manager</p>
            <p>{ productManager || '-' }</p>
        </div>
        <div className="column-one-quarter">
            <p className="heading-small">Delivery manager</p>
            <p>{ deliveryManager || '-' }</p>
        </div>
        <div className="column-one-quarter">
            <p className="heading-small">Service area</p>
            <p>{ serviceArea || '-' }</p>
        </div>
      </div>
    );
  }

  render() {
    return (
      <div id="product-info">
        { this.Status() }
        <h3 className="heading-small">Product description</h3>
        <p>{ this.props.project.description || '-' }</p>
        <h3 className="heading-small">Phase dates</h3>
        { this.PhaseDates() }
        <h3 className="heading-small">Costs</h3>
        { this.Recurring(this.props.project.recurringCosts) }
        { this.OneOff(this.props.project.oneOffCosts) }
        <h3 className="heading-small">Budget</h3>
        { this.Budgets() }
        <h3 className="heading-small">Savings enabled</h3>
        { this.Recurring(this.props.project.recurringSavings) }
        { this.OneOff(this.props.project.oneOffSavings) }
        <h3 className="heading-small">Team description</h3>
        { this.Team() }
      </div>
    );
  }
}
