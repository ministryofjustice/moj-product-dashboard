import 'whatwg-fetch';
import React, { Component } from 'react';
import Spinner from 'react-spinkit';

import { ProductTable } from '../components/product-table';
import { values } from '../libs/utils';
import { getServiceData } from '../libs/models';


/**
 * parse the financial infomation about the service
 */
export function getServiceFinancials(serviceData, productIds) {
  const products = serviceData.products;
  const ids = (typeof productIds === 'undefined') ?
    Object.keys(products) : productIds;
  const serviceFinancials = ids.map(id => products[id].financial);
  let months = serviceFinancials.map(
      productFinancials => Object.keys(productFinancials));
  months = [].concat.apply([], months);
  months = Array.from(new Set(months)).sort();
  const result = {};
  for (const month of months) {
    const monthly = result[month] = {};
    for (const productFinancials of serviceFinancials) {
      const pmf = productFinancials[month] || {};
      Object.keys(pmf).map(key => {
        monthly[key] = (monthly[key] || 0) + parseFloat(pmf[key]);
      });
    };
  };
  return result;
}

/**
 * React component for a service
 */
export class ServiceContainer extends Component {
  constructor(props) {
    super(props);
    this.state = {name: '', products: [], hasData: false};
  }

  componentDidMount() {
    getServiceData(this.props.id)
      .then(serviceData => {
        const products = values(serviceData.products);
        const name = serviceData.name;
        this.setState({products, name, hasData: true});
      });
  }

  render() {
    if (! this.state.hasData) {
      return (
        <div className="spinkit">
          <Spinner
            spinnerName='three-bounce'
          />
        </div>
      );
    };
    return (
      <div>
        <div className="portfolio-header">
          <h1 className="heading-xlarge">
            { this.state.name }
          </h1>
        </div>
        <ProductTable
          products={this.state.products}
          showService={false}
          showFilter={true}
        />
      </div>
    );
  }
}

ServiceContainer.propTypes = {
  id: React.PropTypes.string.isRequired
}
