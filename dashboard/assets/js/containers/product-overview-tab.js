import moment from 'moment';
import React, { Component } from 'react';

import { monthRange, startOfMonth, values, min, max } from '../libs/utils';
import { Product } from '../libs/models';
import { TimeFrameSelector,  KeyStats, ProductGraph } from '../components/product';


export class ProductOverview extends Component {

  get rangeOptions() {
    const timeFrames = this.props.product.timeFrames;
    return Object.keys(timeFrames)
      .map(key => ({
        value: key,
        name: timeFrames[key].name
      }))
  }

  get minStartDate() {
    const candidates = values(this.props.product.timeFrames)
      .map(tf => tf.startDate)
      .filter(date => date != null);
    candidates.push(startOfMonth(this.props.startDate));
    return min(candidates);
  }

  get maxEndDate() {
    const candidates = values(this.props.product.timeFrames)
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
        name: moment(m).format('MMM YY'),
      }));
  }

  get endDateOpts() {
    return monthRange(this.minStartDate, this.maxEndDate, 'end')
      .filter(m => moment(m) >= moment(this.props.startDate) || m == this.props.endDate)
      .map(m => ({
        value: m,
        name: moment(m).format('MMM YY')
      }));
  }

  render() {
    const { product, selectedRange, onRangeChange,
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
          product={ product }
          timeFrame={ selectedRange }
        />
        <ProductGraph
          product={ product }
          isPrinterFriendly={ false }
          onBurnDownChange={ onBurnDownChange }
          showBurnDown={ showBurnDown }
          startDate={ startDate }
          endDate={ endDate }
        />
      </div>
    );
  }
}

ProductOverview.propTypes = {
  product: React.PropTypes.instanceOf(Product).isRequired,
  selectedRange: React.PropTypes.string.isRequired,
  onRangeChange: React.PropTypes.func.isRequired,
  startDate: React.PropTypes.string.isRequired,
  onStartDateChange: React.PropTypes.func.isRequired,
  endDate: React.PropTypes.string.isRequired,
  onEndDateChange: React.PropTypes.func.isRequired,
  showBurnDown: React.PropTypes.bool.isRequired,
  onBurnDownChange: React.PropTypes.func.isRequired
}
