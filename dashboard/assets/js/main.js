import Cookies from 'js-cookie';
import { createHistory } from 'history';
import React from 'react';
import ReactDOM from 'react-dom';

import { ProductContainer } from './containers/product-main';
import { ServiceContainer} from './service';
import { PortfolioContainer } from './portfolio';
import { initCommon } from './common';


import '../styles/gov-uk-elements.css';
import '../styles/main.css';


function project(id) {
  ReactDOM.render(
    <ProductContainer
      type='project'
      id={id}
      csrftoken={Cookies.get('csrftoken')}
    />,
    document.getElementById('container')
  );
}


function service(id) {
  // project table
  ReactDOM.render(
    <ServiceContainer
      id={id}
      csrftoken={Cookies.get('csrftoken')}
    />,
    document.getElementById('container')
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
    <ProductContainer
      type='project-group'
      id={id}
      csrftoken={Cookies.get('csrftoken')}
    />,
    document.getElementById('container')
  );
}


function route(path) {
  // call different loading functions based on page url
  if (path === '/') {
    portfolio();
    return;
  }

  const pattern = /(projects|services|project-groups)(\/(\d+))?/;
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
  };
}


initCommon();
const location = createHistory().getCurrentLocation();
route(location.pathname);
