import moment from 'moment';
import React, { Component } from 'react';
import Plotly from '../plotly-custom';

import { plotCumulativeSpendings } from '../cumulative-graph';
import { plotMonthlySpendings } from '../monthly-graph';
import { numberWithCommas } from '../utils';


const Data = ({data, label}) => (
  <div className="column-one-third">
    <hr/>
    <div className="data">
      <h2 className="bold-xlarge">{data}</h2>
      <p className="bold-xsmall">{label}</p>
    </div>
  </div>
);

export function TimeFrameSelector({
  rangeOptions,
  selectedRange,
  onRangeChange,
  startDateOpts,
  selectedStartDate,
  onStartDateChange,
  endDateOpts,
  selectedEndDate,
  onEndDateChange}) {

  return (
    <div className="grid-row date-range">
      <div className="column-one-quarter">
        <label className="form-label" htmlFor="form-field-name">
          Show data for
        </label>
        <select className="form-control form-control-1-1" id="form-field-name" name="form-field-name" value={selectedRange || ''} onChange={onRangeChange}>
        {
          rangeOptions.map((option, index) => (
            <option value={option.value} key={index}>{option.name}</option>)
          )
        }
        </select>
      </div>
      <div className="column-one-quarter">
        <label className="form-label" htmlFor="start-date">
          From beginning of
        </label>
        <select className="form-control form-control-1-1" id="start-date" name="start-date" value={selectedStartDate || ''} onChange={onStartDateChange}>
          {
            startDateOpts.map((option, index) => (
              <option value={option.value} key={index}>{option.name}</option>)
            )
          }
        </select>
      </div>
      <div className="column-one-quarter">
        <label className="form-label" htmlFor="end-date">
          To end of
        </label>
        <select className="form-control form-control-1-1" id="end-date" name="end-date" value={selectedEndDate || ''} onChange={onEndDateChange}>
          {
            endDateOpts.map((option, index) => (
              <option value={option.value} key={index}>{option.name}</option>)
            )
          }
        </select>
      </div>
    </div>
  );
}


export function KeyStats({project, timeFrame, startDate, endDate}) {
  let budget = 0;
  let spend= 0;
  let savings = 0;
  let phaseName = null
  if (timeFrame in project.phases) {
    phaseName = project.phases[timeFrame].name;
    ({ budget, spend, savings } = project.statsInPhase(timeFrame));
  } else {
    const startMonth = moment(startDate, 'YYYY-MM-DD').format('YYYY-MM');
    const endMonth = moment(endDate, 'YYYY-MM-DD').format('YYYY-MM');
    ({ budget, spend, savings } = project.statsBetween(startMonth, endMonth));
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

  return (
    <div className="project-row">
      <h4 className="heading-medium">Key statistics</h4>
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

export class ProductGraph extends Component {

  svg2png(svgPromise, elem) {
    return svgPromise
      .then((gd) => Plotly.toImage(gd, {format:'png'}))
      .then((url) => elem.setAttribute('src', url));
  }

  plot() {
    const cumulativeSpendings = plotCumulativeSpendings(
      this.props.project,
      this.props.showBurnDown,
      this.props.startDate,
      this.props.endDate,
      this.svg1
    );
    this.svg2png(cumulativeSpendings, this.png1);

    const monthlySpendings = plotMonthlySpendings(
      this.props.project,
      this.props.startDate,
      this.props.endDate,
      this.svg2
    );
    this.svg2png(monthlySpendings, this.png2);
  }

  componentDidUpdate() {
    this.plot();
  }

  componentDidMount() {
    this.plot();
  }

  BurnDownToggle() {
    return (
      <div>
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
      </div>
    );
  }

  render() {
    return (
      <div className="project-row">
        <h4 className="heading-medium">Total expenditure and budget</h4>
        <hr/>
        { this.props.showToggle ? this.BurnDownToggle() : null }
        <div className="plotly-graph-svg" ref={(elem) => this.svg1=elem} />
        {/* png is hidden for display and visible for printing */}
        <img className="plotly-graph-png" ref={(elem) => this.png1=elem} />
        <h4 className="heading-medium">Monthly expenditure</h4>
        <hr/>
        <div className="plotly-graph-svg" ref={(elem) => this.svg2=elem} />
        {/* png is hidden for display and visible for printing */}
        <img className="plotly-graph-png" ref={(elem) => this.png2=elem} />
      </div>
    );
  }
}


export function PhaseTag({phase}) {
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


export function RagTag({rag}) {
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


export const TimeFrameDisplay = ({ timeFrame, startDate, endDate }) => (
  <div className="grid-row">
    <div className="column-one-third">
      <p className="heading-small">Data for</p>
      <p>{ timeFrame }</p>
    </div>
    <div className="column-one-third">
      <p className="heading-small">From beginning of</p>
      <p>{ moment(startDate).format('MMM YY') }</p>
    </div>
    <div className="column-one-third">
      <p className="heading-small">To end of</p>
      <p>{ moment(endDate).format('MMM YY') }</p>
    </div>
  </div>
);


export const PrintModeToggle = ({isPrintMode, onClick}) => (
  <a className="print-label" onClick={ onClick }>
    { isPrintMode ? 'Switch to normal mode' : 'Switch to print mode' }
  </a>
);
