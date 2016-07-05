import 'whatwg-fetch';
import React, { Component } from 'react';
import Spinner from 'react-spinkit';

import { ProjectsTable } from './project';
import { values } from './utils';


/**
 * send a POST request to the backend to retrieve projects profile
 */
export function getPortfolioData(id, csrftoken) {
  const init = {
    credentials: 'same-origin',
    method: 'GET',
  };
  return fetch('/portfolio.json', init)
    .then(response => response.json());
}

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
        const projects = values(portfolioData)
          .map(service => values(service.projects))
          .reduce((prev, curr) => prev.concat(curr), []);
        this.setState({projects: projects, hasData: true});
      });
  }

  render() {
    if (! this.state.hasData) {
      return (
        <div className="projects-spinkit">
          <Spinner
            spinnerName='three-bounce'
          />
        </div>
      );
    };
    return (
      <div>
        <label className="heading-medium">
          <strong>Portfolio</strong>
        </label>
        <ProjectsTable
          projects={this.state.projects}
          showService={true}
          showFilter={true}
        />
      </div>
    );
  }
}
