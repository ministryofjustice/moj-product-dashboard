import $ from 'jquery';
import select2 from 'select2';
import Cookies from 'js-cookie';
import { createHistory } from 'history';
import React from 'react';
import ReactDOM from 'react-dom';

import { ProjectContainer } from './project';
import { ServiceContainer} from './service';
import { PortfolioContainer } from './portfolio';


require('select2/dist/css/select2.min.css');
require('../styles/gov-uk-elements.css');
require('../styles/main.css');


function project(id) {
  ReactDOM.render(
    <ProjectContainer id={id} csrftoken={Cookies.get('csrftoken')} />,
    document.getElementById('fig-a')
  );

  // dropdown project selector
  $('#projects').select2().on("select2:select", (e) => {
    const projectId = e.params.data.id;
    window.location.href = `/projects/${projectId}`;
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
    document.getElementById('projects')
  );
}


function route(path) {
  // call different loading functions based on page url
  const pattern = /(projects|services|portfolio)(\/(\d+))?/;
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
    case 'portfolio':
      portfolio();
      break;
  };
}


const location = createHistory().getCurrentLocation();
route(location.pathname);
