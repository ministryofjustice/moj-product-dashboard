import { createHistory } from 'history';
import React from 'react';
import ReactDOM from 'react-dom';

import { ProductContainer } from './containers/product-main';
import { ServiceContainer} from './containers/service';
import { PortfolioContainer } from './containers/portfolio';

import '../styles/gov-uk-elements.css';
import '../styles/main.css';


function product(id) {
  ReactDOM.render(
    <ProductContainer type='product' id={id} />,
    document.getElementById('container')
  );
}


function service(id) {
  // product table
  ReactDOM.render(
    <ServiceContainer id={id} />,
    document.getElementById('container')
  );
}


function portfolio() {
  // product table
  ReactDOM.render(
    <PortfolioContainer />,
    document.getElementById('container')
  );
}


function productGroup(id) {
  ReactDOM.render(
    <ProductContainer type='product-group' id={id} />,
    document.getElementById('container')
  );
}


function route(path) {
  // call different loading functions based on page url
  if (path === '/') {
    portfolio();
    return;
  }

  const pattern = /(products|services|product-groups)(\/(\d+))?/;
  const matches = pattern.exec(path);

  if (matches === null)
    return;

  const [_0, endpoint, _1, id] = matches;

  switch (endpoint) {
    case 'products':
      product(id);
      break;
    case 'services':
      service(id);
      break;
    case 'product-groups':
      productGroup(id);
      break;
  };
}


const location = createHistory().getCurrentLocation();
route(location.pathname);
