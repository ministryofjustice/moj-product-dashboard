import 'whatwg-fetch';
import React, { Component } from 'react';

import { ProjectsTable } from './project';
import { values } from './utils';

/**
 * send a POST request to the backend to retrieve projects profile
 */
export function getPortfolioData(id, csrftoken) {
  const init = {
    credentials: 'same-origin',
    method: 'POST',
    headers: {
      'X-CSRFToken': csrftoken,
      'Accept': 'application/json',
      'Content-Type': 'application/json'
    }
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
    this.state = {projects: []};
  }

  componentDidMount() {
    getPortfolioData(this.props.id, this.props.csrftoken)
      .then(portfolioData => {
        const projects = values(portfolioData)
          .map(service => values(service.projects))
          .reduce((prev, curr) => prev.concat(curr), []);
        this.setState({projects: projects});
      });
  }

  render() {
    return (
      <ProjectsTable
        projects={this.state.projects}
        showService={true}
        showFilter={true}
      />
    );
  }
}
