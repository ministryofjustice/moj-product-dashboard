import moment from 'moment';
import React, { Component } from 'react';

import { monthRange, startOfMonth, values, numberWithCommas, min, max } from './utils';
import { plotCumulativeSpendings } from './cumulative-graph';
import { plotMonthlySpendings } from './monthly-graph';


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
            <option value={option.value} key={index}>{option.children}</option>)
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
              <option value={option.value} key={index}>{option.children}</option>)
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
              <option value={option.value} key={index}>{option.children}</option>)
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

export class ProjectGraph extends Component {

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
      <div className="project-row">
        <h4 className="heading-medium">Total expenditure and budget</h4>
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
        <div className="project-row" ref={(elem) => this.container1=elem} />
        <h4 className="heading-medium">Monthly expenditure</h4>
        <hr/>
        <div ref={(elem) => this.container2=elem} />
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


export class ProductOverview extends Component {

  get rangeOptions() {
    const timeFrames = this.props.project.timeFrames;
    return Object.keys(timeFrames)
      .map(key => ({
        value: key,
        children: timeFrames[key].name
      }))
  }

  get minStartDate() {
    const candidates = values(this.props.project.timeFrames)
      .map(tf => tf.startDate)
      .filter(date => date != null);
    candidates.push(startOfMonth(this.props.startDate));
    return min(candidates);
  }

  get maxEndDate() {
    const candidates = values(this.props.project.timeFrames)
      .map(tf => tf.endDate)
      .filter(date => date != null);
    candidates.push(startOfMonth(this.props.endDate));
    return max(candidates);
  }

  get startDateOpts() {
    return monthRange(this.minStartDate, this.maxEndDate, 'start')
      .filter(m => moment(m) <= moment(this.props.endDate) || m == this.props.startDate)
      .map(m => ({
        value: m,
        children: moment(m).format('MMM YY'),
      }));
  }

  get endDateOpts() {
    return monthRange(this.minStartDate, this.maxEndDate, 'end')
      .filter(m => moment(m) >= moment(this.props.startDate) || m == this.props.endDate)
      .map(m => ({
        value: m,
        children: moment(m).format('MMM YY')
      }));
  }

  render() {
    const { project, selectedRange, onRangeChange,
    startDate, onStartDateChange,
    endDate, onEndDateChange,
    showBurnDown, onBurnDownChange }  = this.props;
    return (
      <div>
        <TimeFrameSelector rangeOptions={ this.rangeOptions }
          selectedRange={ selectedRange }
          onRangeChange={ onRangeChange }
          selectedStartDate={ startDate }
          selectedEndDate={ endDate }
          startDateOpts={ this.startDateOpts }
          endDateOpts={ this.endDateOpts }
          onStartDateChange={ onStartDateChange }
          onEndDateChange={ onEndDateChange }
        />
        <KeyStats
          startDate={ startDate }
          endDate={ endDate }
          project={ project }
          timeFrame={ selectedRange }
        />
        <ProjectGraph
          project={ project }
          onBurnDownChange={ onBurnDownChange }
          showBurnDown={ showBurnDown }
          startDate={ startDate }
          endDate={ endDate }
        />
      </div>
    );
  }
}
