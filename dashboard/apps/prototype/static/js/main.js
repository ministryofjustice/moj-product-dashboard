import $ from 'jquery';
import select2 from 'select2';
import Cookies from 'js-cookie';
import {getProjectData, plotProject} from './project';
import { createHistory } from 'history';

require('select2/dist/css/select2.min.css');
require('../styles/gov-uk-elements.css');
require('../styles/main.css');


function project(id) {
  // get the DOM element for the graph
  const elem = document.getElementById('fig-a');
  // plot the project
  getProjectData(id, Cookies.get('csrftoken'))
    .then(projectData => plotProject(projectData, elem));

  // dropdown project selector
  $('#projects').select2().on("select2:select", (e) => {
    const projectId = e.params.data.id;
    window.location.href = `/projects/${projectId}`;
  });
}


function service(id) {
  // dropdown serviceselector
  $('#services').select2().on("select2:select", (e) => {
    const serviceId = e.params.data.id;
    window.location.href = `/services/${serviceId}`;
  });
}


function route(path) {
  // call different loading functions based on page url
  const pattern = /(projects|services)\/(\d+)/;
  const matches = pattern.exec(path);

  if (matches === null)
    return;

  const [_, endpoint, id] = matches;

  switch (endpoint) {
    case 'projects':
      project(id);
    case 'services':
      service(id);
  };
}


const location = createHistory().getCurrentLocation();
route(location.pathname);
