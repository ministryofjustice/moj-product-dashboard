import React, { Component } from 'react';
import Spinner from 'react-spinkit';

import { ProductTable } from '../components/product-table';
import { getPortfolioData } from '../libs/models';
import { values } from '../libs/utils';


/**
 * React component for portfolio
 */
export class PortfolioContainer extends Component {
  constructor(props) {
    super(props);
    this.state = {projects: [], hasData: false};
  }

  componentDidMount() {
    getPortfolioData(this.props.id, this.props.csrftoken)
      .then(portfolioData => {
        // sort by service area and then name of product
        const projects = values(portfolioData)
          .sort((s1, s2) => s1.name.localeCompare(s2.name))
          .map(service => values(service.projects).sort(
                (p1, p2) => p1.name.localeCompare(p2.name)))
          .reduce((prev, curr) => prev.concat(curr), []);
        this.setState({projects: projects, hasData: true});

        // hack to set the id of the input so that the label attaches to it
        document.getElementsByName('filter')[0].setAttribute('id', 'filter-results');
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
            MoJ Digital Portfolio
          </h1>
          <label className="form-label" htmlFor="filter-results">
            Filter results
          </label>
        </div>
        <ProductTable
          projects={this.state.projects}
          showService={true}
          showFilter={true}
        />
      </div>
    );
  }
}