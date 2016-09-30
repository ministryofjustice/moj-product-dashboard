import React, { Component } from 'react';

import { KeyStats, ProductGraph, TimeFrameDisplay } from '../components/product';
import { Product } from '../libs/models';
import { ProductInfo } from './product-info-tab';


export function ProductPrintMode({ product, selectedRange, startDate, endDate, showBurnDown }) {
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

ProductPrintMode.propTypes = {
  product: React.PropTypes.instanceOf(Product).isRequired,
  selectedRange: React.PropTypes.string.isRequired,
  startDate: React.PropTypes.string.isRequired,
  endDate: React.PropTypes.string.isRequired,
  showBurnDown: React.PropTypes.bool.isRequired
}
