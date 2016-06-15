import $ from 'jquery';
import select2 from 'select2';
import Cookies from 'js-cookie';
import URI from 'urijs';
import {getProjectData, plotProject} from './project';

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

function area(id) {
  // dropdown area selector
  $('#areas').select2().on("select2:select", (e) => {
    const areaId = e.params.data.id;
    window.location.href = `/areas/${areaId}`;
  });
}

function route(path) {
  // call different loading functions based on page url
  const pattern = /(projects|areas)\/(\d+)/;
  const matches = pattern.exec(path);

  if (matches === null) return;

  switch (matches[1]) {
    case 'projects':
      project(matches[2]);
    case 'areas':
      area(matches[2]);
  };
}

$(() => {
  const path = URI(window.location.href).path();
  route(path);
});
