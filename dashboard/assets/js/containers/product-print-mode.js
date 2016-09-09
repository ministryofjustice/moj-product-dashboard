import moment from 'moment';
import React, { Component } from 'react';

import { monthRange, startOfMonth, values, min, max } from '../libs/utils';
import { TimeFrameSelector, KeyStats, ProductGraph, TimeFrameDisplay } from '../components/product';
import { ProductInfo } from './product-info-tab';


export class ProductPrintMode extends Component {

  render() {
    const { project, selectedRange, startDate, endDate, showBurnDown }  = this.props;
    return (
      <div>
        <TimeFrameDisplay
          timeFrame={ project.timeFrames[selectedRange].name }
          startDate={ startDate }
          endDate={ endDate }
        />
        <KeyStats
          startDate={ startDate }
          endDate={ endDate }
          project={ project }
          timeFrame={ selectedRange }
        />
        <ProductGraph
          project={ project }
          showToggle={ false }
          showBurnDown={ showBurnDown }
          startDate={ startDate }
          endDate={ endDate }
        />
        <ProductInfo project={ project } />
      </div>
    );
  }
}
