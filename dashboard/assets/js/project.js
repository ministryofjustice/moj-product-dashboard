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
         startOfMonth, endOfMonth,
         min, max, values, round, numberWithCommas } from './utils';
import { plotCumulativeSpendings } from './cumulative-graph';

import RedImg from '../img/red.png';
import AmberImg from '../img/amber.png';
import GreenImg from '../img/green.png';
import OKImg from '../img/ok.png';
import AtRiskImg from '../img/at-risk.png';
import InTroubleImg from '../img/in-trouble.png';
import SeparatorImg from '../img/separator.png';

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
    return {
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

    if (typeof this.state.project.name === 'undefined') {
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
        <div className="breadcrumbs">
          <ol>
            <li>
              <a href="/">Digital portfolio</a>
            </li>
            <li style={{ backgroundImage: `url(${SeparatorImg})` }}>
              { this.state.project.name }
            </li>
          </ol>
        </div>
        <h1 className="heading-xlarge">
          <div className="banner">
            <PhaseTag phase={this.state.project.phase } />
            <RagTag rag={this.state.project.rag} />
          </div>
          {this.state.project.name}
        </h1>
        <Tabs className="product-tabs">
          <TabList>
            <Tab>Overview</Tab>
            <Tab>Product information</Tab>
          </TabList>
          <TabPanel>
            { timeFrameSelector }
            <KeyStats
              startDate={this.state.startDate}
              endDate={this.state.endDate}
              project={this.state.project}
            />
            <ProjectGraph
              project={this.state.project}
              onBurnDownChange={(e) => this.handleBurnDownChange(e)}
              showBurnDown={this.state.showBurnDown}
              startDate={this.state.startDate}
              endDate={this.state.endDate}
            />
          </TabPanel>
          <TabPanel>
            <p>{ this.state.project.description }</p>
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


function KeyStats({project, startDate, endDate}) {
  let budget = 0;
  let spend= 0;
  let savings = 0;
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

  const budgetLabel = (endDate) => {
    if (endDate === null) {
      return 'Budget';
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
          label={budgetLabel(endDate)}
        />
        <Data
          data={format(spend)}
          label="Spend for this period"
        />
        <Data
          data={format(savings)}
          label="Savings enabled for this period"
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
        const mapping = {
          'OK': OKImg,
          'At risk': AtRiskImg,
          'In trouble': InTroubleImg
        };
        return (
            <img src={ mapping[props.data] } className="status" alt={props.data} />
          )}
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
    },
    {
      'columnName': 'budget',
      'order': 7,
      'displayName': 'Budget',
      'customCompareFn': Number,
      'customComponent': displayMoney,
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

  get monthlyFinancials() {
    return parseProjectFinancials(this.data.financial);
  }
}
