import React, { Component } from 'react';
import Spinner from 'react-spinkit';
import { Tab, Tabs, TabList, TabPanel } from 'react-tabs';

import { Product, getProductData } from '../libs/models';
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
      product: new Product({}),
      timeFrame: 'entire-time-span',
      startDate: null,
      endDate: null,
      isPrintMode: false
    };
    Tabs.setUseDefaultStyles(false);
  }

  componentDidMount() {
    getProductData(this.props.type, this.props.id, this.props.csrftoken)
      .then(productJSON => {
        const product = new Product(productJSON);
        this.setState({
          product: product,
          startDate: product.firstDate,
          endDate: product.lastDate,
          hasData: true
        });
      });
  }

  handleBurnDownChange(e) {
    this.setState({showBurnDown: e.target.value == 'burn-down'});
  }

  handleTimeFrameChange(evt) {
    const timeFrame = evt.target.value;
    const state = {timeFrame: timeFrame};
    const { startDate, endDate } = this.state.product.timeFrames[timeFrame];
    // startDate can be null e.g. for 'custome range'
    if (startDate) {
      state.startDate = startDate
    };
    // endDate can be null e.g. for 'custome range'
    if (endDate) {
      state.endDate = endDate
    };
    this.setState(state);
  }

  handleStartDateChange(evt) {
    const startDate = evt.target.value;
    this.setState({
      startDate: startDate,
      timeFrame: this.state.product.matchTimeFrame(startDate, this.state.endDate)
    });
  }

  handleEndDateChange(evt) {
    const endDate = evt.target.value;
    this.setState({
      endDate: endDate,
      timeFrame: this.state.product.matchTimeFrame(this.state.startDate, endDate)
    });
  }

  handleTogglePrintMode(evt) {
    this.setState({isPrintMode: !this.state.isPrintMode});
  }

  normalMode() {
    const product = this.state.product;
    const editButton = () => {
      if (product.meta['can_edit']) {
        return (
          <a className="button" href={ product.meta['admin_url'] }>
            Edit product details
          </a>
        );
      }
      return null;
    }
    return (
      <div>
        <div className="breadcrumbs">
          <ol>
            <li>
              <a href="/">Portfolio Summary</a>
            </li>
            <li style={{ backgroundImage: `url(${SeparatorImg})` }}>
              { product.name }
            </li>
          </ol>
        </div>
        <h1 className="heading-xlarge" id="product-heading">
          <div className="banner">
            <PhaseTag phase={ product.phase } />
            <RagTag rag={ product.rag } />
          </div>
          {product.name}
          { editButton() }
        </h1>
        <Tabs className="product-tabs">
          <TabList>
            <Tab><span className="font-small">Overview</span></Tab>
            <Tab><span className="font-small">Product information</span></Tab>
          </TabList>
          <TabPanel>
            <ProductOverview
              product={product}
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
            <ProductInfo product={ product } />
          </TabPanel>
        </Tabs>
        <hr/>
        <PrintModeToggle
          isPrintMode={ this.state.isPrintMode }
          onClick = { (evt) => this.handleTogglePrintMode(evt) }
        />
      </div>
    );
  }

  printMode() {
    const product = this.state.product;
    return (
      <div>
        <h1 className="heading-xlarge">
          <div className="banner">
            <PhaseTag phase={ product.phase } />
            <RagTag rag={ product.rag } />
          </div>
          {product.name}
        </h1>
        <ProductPrintMode
          product={product}
          onRangeChange={evt => this.handleTimeFrameChange(evt)}
          selectedRange={this.state.timeFrame}
          startDate={this.state.startDate}
          endDate={this.state.endDate}
          onStartDateChange={evt => this.handleStartDateChange(evt)}
          onEndDateChange={evt => this.handleEndDateChange(evt)}
          onBurnDownChange={ (e) => this.handleBurnDownChange(e) }
          showBurnDown={ this.state.showBurnDown }
        />
        <hr/>
        <PrintModeToggle
          isPrintMode={ this.state.isPrintMode }
          onClick = { (evt) => this.handleTogglePrintMode(evt) }
        />
      </div>
    );
  }

  render() {
    if (typeof this.state.product.name === 'undefined') {
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

ProductContainer.propTypes = {
  type: React.PropTypes.string.isRequired,
  id: React.PropTypes.string.isRequired,
  csrftoken: React.PropTypes.string.isRequired
}
