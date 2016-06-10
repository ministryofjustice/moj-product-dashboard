import $ from 'jquery';
import select2 from 'select2';
import {getProjectId, getProjectURL, getProjectData, plotProject} from './project';

require('select2/dist/css/select2.min.css');
require('../styles/gov-uk-elements.css');
require('../styles/main.css');

$(() => {
  // get the DOM element for the graph
  const elem = document.getElementById('fig-a');
  // get the projectId
  const projectId = getProjectId(window.location.href);
  // plot the project
  getProjectData(projectId)
    .then(projectData => plotProject(projectData, elem));

  // dropdown project selector
  $('#projects').select2().on("select2:select", (e) => {
    const projectid = e.params.data.id;
    const projectURL = getProjectURL(window.location.href, projectid);
    window.location.href = projectURL;
  });
});
