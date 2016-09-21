import moment from 'moment';
import React, { Component } from 'react';

import { monthRange, startOfMonth, values, min, max } from '../libs/utils';
import { TimeFrameSelector, KeyStats, ProductGraph, TimeFrameDisplay } from '../components/product';
import { ProductInfo } from './product-info-tab';


export class ProductPrintMode extends Component {

  render() {
    const { product, selectedRange, startDate, endDate, showBurnDown }  = this.props;
    return (
      <div>
        <TimeFrameDisplay
          timeFrame={ product.timeFrames[selectedRange].name }
          startDate={ startDate }
          endDate={ endDate }
        />
        <KeyStats
          startDate={ startDate }
          endDate={ endDate }
          product={ product }
          timeFrame={ selectedRange }
        />
        <ProductGraph
          product={ product }
          isPrinterFriendly={ true }
          showBurnDown={ showBurnDown }
          startDate={ startDate }
          endDate={ endDate }
        />
        <ProductInfo product={ product } />
      </div>
    );
  }
}
