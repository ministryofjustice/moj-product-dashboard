import 'whatwg-fetch';
import moment from 'moment';
import Griddle from 'griddle-react';
import React, { Component } from 'react';
import Spinner from 'react-spinkit';
import Select from 'react-select-plus';

import Plotly from './plotly-custom';

/**
 * send a POST request to the backend to retrieve project profile
 */
export function getProjectData(id, timeFrame, csrftoken) {
  const init = {
    credentials: 'same-origin',
    method: 'POST',
    headers: {
      'X-CSRFToken': csrftoken,
      'Accept': 'application/json',
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({id: id, timeFrame: timeFrame})
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
      timeFrame: this.timeFrameOptions[0].value
    };
  }

  get timeFrameOptions() {
    return [
      { value: 'entire-time-span', label: 'Entire project life time' },
      { value: 'this-year', label: 'This calendar year' },
      { value: 'this-financial-year', label: 'This financial year' },
      { value: 'this-quarter', label: 'This quarter' },
      { value: 'last-year', label: 'Last calendar year' },
      { value: 'last-financial-year', label: 'Last financial year' },
      { value: 'last-quarter', label: 'Last quarter' },
    ];
  }

  componentDidMount() {
    getProjectData(this.props.id, this.state.timeFrame, this.props.csrftoken)
      .then(project => {
        this.setState({project: project, hasData: true});
      });
  }

  handleToggle() {
    this.setState({showRemainings: !this.state.showRemainings});
  }

  componentWillUpdate(nextProps, nextState) {
    const timeFrame = nextState.timeFrame;
    if (this.state.timeFrame != timeFrame) {
      getProjectData(this.props.id, timeFrame, this.props.csrftoken)
        .then(project => {
          this.setState({project: project, hasData: true});
        });
    }
  }

  handleTimeFrameChange(selection) {
    if (selection && this.state.timeFrame != selection.value) {
      this.setState({
        timeFrame: selection.value,
        hasData: false
      });
    }
  }

  render() {
    const timeFrameSelector = (
      <TimeFrameSelector
        options={this.timeFrameOptions}
        selected={this.state.timeFrame}
        onChange={selection => this.handleTimeFrameChange(selection)}
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


const TimeFrameSelector = ({options, selected, onChange}) => (
  <div className="grid-row">
    <div className="column-one-quarter">
      <label>Time frame</label>
    </div>
    <div className="column-one-quarter">
      <Select
        clearable={false}
        placeholder="Select time frame"
        name="form-field-name"
        value={selected}
        options={options}
        onChange={onChange}
      />
    </div>
  </div>
);


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
