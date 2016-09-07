import React, { Component } from 'react';
import Spinner from 'react-spinkit';
import { Tab, Tabs, TabList, TabPanel } from 'react-tabs';

import { Project, getProjectData } from '../models';
import { PhaseTag, RagTag, PrintModeToggle } from '../components/product';
import { ProductOverview } from './product-overview-tab';
import { ProductInfo } from './product-info-tab';
import { ProductPrintMode } from './product-print-mode';

import SeparatorImg from '../../img/separator.png';

export class ProductContainer extends Component {

  constructor(props) {
    super(props);
    this.state = {
      showBurnDown: false,
      hasData: false,
      project: new Project({}),
      timeFrame: 'entire-time-span',
      startDate: null,
      endDate: null,
      isPrintMode: false
    };
    Tabs.setUseDefaultStyles(false);
  }

  componentDidMount() {
    const { startDate, endDate } = this.state.project.timeFrames[this.state.timeFrame];
    getProjectData(this.props.type, this.props.id, startDate, endDate, this.props.csrftoken)
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

  handleTimeFrameChange(evt) {
    const newVal = evt.target.value;
    const { startDate, endDate } = this.state.project.timeFrames[newVal];
    this.setState({
      startDate: startDate,
      endDate: endDate,
      timeFrame: newVal
    });
  }

  handleStartDateChange(evt) {
    const startDate = evt.target.value;
    this.setState({
      startDate: startDate,
      timeFrame: this.state.project.matchTimeFrame(startDate, this.state.endDate)
    });
  }

  handleEndDateChange(evt) {
    const endDate = evt.target.value;
    this.setState({
      endDate: endDate,
      timeFrame: this.state.project.matchTimeFrame(this.state.startDate, endDate)
    });
  }

  handleTogglePrintMode(evt) {
    this.setState({isPrintMode: !this.state.isPrintMode});
  }

  normalMode() {
    const project = this.state.project;
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
            <ProductOverview
              project={project}
              onRangeChange={evt => this.handleTimeFrameChange(evt)}
              selectedRange={this.state.timeFrame}
              startDate={this.state.startDate}
              endDate={this.state.endDate}
              onStartDateChange={evt => this.handleStartDateChange(evt)}
              onEndDateChange={evt => this.handleEndDateChange(evt)}
              onBurnDownChange={ (e) => this.handleBurnDownChange(e) }
              showBurnDown={ this.state.showBurnDown }
            />
          </TabPanel>
          <TabPanel>
            <ProductInfo project={ project } />
          </TabPanel>
        </Tabs>
        <PrintModeToggle
          isPrintMode={ this.state.isPrintMode }
          onClick = { (evt) => this.handleTogglePrintMode(evt) }
        />
      </div>
    );
  }

  printMode() {
    const project = this.state.project;
    return (
      <div>
        <h1 className="heading-xlarge">
          <div className="banner">
            <PhaseTag phase={ project.phase } />
            <RagTag rag={ project.rag } />
          </div>
          {project.name}
        </h1>
        <ProductPrintMode
          project={project}
          onRangeChange={evt => this.handleTimeFrameChange(evt)}
          selectedRange={this.state.timeFrame}
          startDate={this.state.startDate}
          endDate={this.state.endDate}
          onStartDateChange={evt => this.handleStartDateChange(evt)}
          onEndDateChange={evt => this.handleEndDateChange(evt)}
          onBurnDownChange={ (e) => this.handleBurnDownChange(e) }
          showBurnDown={ this.state.showBurnDown }
        />
        <PrintModeToggle
          isPrintMode={ this.state.isPrintMode }
          onClick = { (evt) => this.handleTogglePrintMode(evt) }
        />
      </div>
    );
  }

  render() {
    if (typeof this.state.project.name === 'undefined') {
      return (
        <div>
          <div className="spinkit">
            <Spinner spinnerName='three-bounce' />
          </div>
        </div>
      );
    };
    if (this.state.isPrintMode) {
      return this.printMode();
    }
    return this.normalMode();
  }
}
