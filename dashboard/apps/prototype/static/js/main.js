import $ from 'jquery';
import select2 from 'select2';
import Cookies from 'js-cookie';
import { createHistory } from 'history';
import React from 'react';
import ReactDOM from 'react-dom';

import { ProjectContainer } from './project';
import { ServiceContainer} from './service';
import { PortfolioContainer } from './portfolio';
import { initCommon } from './common';


import 'select2/dist/css/select2.min.css';
import '../styles/gov-uk-elements.css';
import '../styles/main.css';


function project(id) {
  ReactDOM.render(
    <ProjectContainer
      type='project'
      id={id}
      csrftoken={Cookies.get('csrftoken')}
    />,
    document.getElementById('fig-a')
  );

  // dropdown project selector
  $('#projects').select2().on("select2:select", (e) => {
    window.location.href = e.params.data.id;
  });
}


function service(id) {
  // dropdown service selector
  $('#services').select2().on("select2:select", (e) => {
    const serviceId = e.params.data.id;
    window.location.href = `/services/${serviceId}`;
  });

  // project table
  ReactDOM.render(
    <ServiceContainer
      id={id}
      csrftoken={Cookies.get('csrftoken')}
    />,
    document.getElementById('projects')
  );
}


function portfolio() {
  // project table
  ReactDOM.render(
    <PortfolioContainer csrftoken={Cookies.get('csrftoken')} />,
    document.getElementById('container')
  );
}


function projectGroup(id) {
  ReactDOM.render(
    <ProjectContainer
      type='project-group'
      id={id}
      csrftoken={Cookies.get('csrftoken')}
    />,
    document.getElementById('container')
  );
  // dropdown project selector
  $('#projects').select2().on("select2:select", (e) => {
    window.location.href = e.params.data.id;
  });
}


function route(path) {
  // call different loading functions based on page url
  const pattern = /(projects|services|project-groups|portfolio)(\/(\d+))?/;
  const matches = pattern.exec(path);

  if (matches === null)
    return;

  const [_0, endpoint, _1, id] = matches;

  switch (endpoint) {
    case 'projects':
      project(id);
      break;
    case 'services':
      service(id);
      break;
    case 'project-groups':
      projectGroup(id);
      break;
    case 'portfolio':
      portfolio();
      break;
  };
}


initCommon();
const location = createHistory().getCurrentLocation();
route(location.pathname);
