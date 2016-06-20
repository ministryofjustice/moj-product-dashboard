import 'whatwg-fetch';


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
