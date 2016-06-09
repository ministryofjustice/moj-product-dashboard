'use strict';
import Cookies from 'js-cookie';
import 'whatwg-fetch';
import URI from 'urijs';
import moment from 'moment';
import _ from 'lodash';

/**
 * send a POST request to the backend to retrieve project profile
 */
export function getProjectData(id) {
  return fetch('/project.json', {
    credentials: 'same-origin',
    method: 'POST',
    headers: {
      'X-CSRFToken': Cookies.get('csrftoken'),
      'Accept': 'application/json',
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({projectid: id})
  }).then(response => response.json());
}

/**
 * parse the financial infomation about the project
 */
export function parseProjectFinancials(financial) {
  let [months, costs] = _(financial).toPairs().sort().unzip().value();
  months = months.map(m => moment(m, 'YYYY-MM').format('MMM YY'));

  const _mapFloat = key => costs.map(c => parseFloat(c[key]));
  const contractorCosts = _mapFloat('contractor');
  const civilServantCosts = _mapFloat('non-contractor');
  const additionalCosts = _mapFloat('additional');
  const budget = _mapFloat('budget');
  
  const totalCosts = _.zip(contractorCosts, civilServantCosts, additionalCosts)
                      .map(([x, y, a]) => x + y + a);
  const totalCostsCumulative = [];
  totalCosts.reduce((x, y, i) => totalCostsCumulative[i] = x + y, 0);

  return {
    months,
    budget,
    civilServantCosts,
    contractorCosts,
    additionalCosts,
    totalCostsCumulative
  };
}


/**
 * get projectId based on the query string
 */
export function getProjectId() {
  return URI(window.location.href).query(true).projectid;
}


/**
 * load the page for the project based on id
 **/
export function loadProjectPage(id) {
  const url = [location.protocol, '//', location.host, location.pathname].join('');
  window.location.href = url + '?projectid=' + id;
}
