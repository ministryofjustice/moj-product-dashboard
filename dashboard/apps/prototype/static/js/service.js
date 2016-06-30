import 'whatwg-fetch';
import React, { Component } from 'react';

import { ProjectsTable } from './project';
import { values } from './utils';


/**
 * send a POST request to the backend to retrieve service area profile
 */
export function getServiceData(id, csrftoken) {
  const init = {
    credentials: 'same-origin',
    method: 'POST',
    headers: {
      'X-CSRFToken': csrftoken,
      'Accept': 'application/json',
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({id: id})
  };
  return fetch('/service.json', init)
    .then(response => response.json());
}


/**
 * parse the financial infomation about the service
 */
export function getServiceFinancials(serviceData, projectIds) {
  const projects = serviceData.projects;
  const ids = (typeof projectIds === 'undefined') ?
    Object.keys(projects) : projectIds;
  const serviceFinancials = ids.map(id => projects[id].financial);
  let months = serviceFinancials.map(
      projectFinancials => Object.keys(projectFinancials));
  months = [].concat.apply([], months);
  months = Array.from(new Set(months)).sort();
  const result = {};
  for (const month of months) {
    const monthly = result[month] = {};
    for (const projectFinancials of serviceFinancials) {
      const pmf = projectFinancials[month] || {};
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
    this.state = {projects: []};
  }

  componentDidMount() {
    getServiceData(this.props.id, this.props.csrftoken)
      .then(serviceData => {
        const projects = values(serviceData.projects);
        this.setState({projects: projects});
      });
  }

  render() {
    return (
      <ProjectsTable projects={this.state.projects} />
    );
  }
}
