import Cookies from 'js-cookie';


/*
 * get the values of an object as an array
 */
export function values(obj) {
  return Object.keys(obj).map(key => obj[key]);
}

/**
 * send a POST request to the backend
 */
export function postToBackend(url, body) {
  const init = {
    credentials: 'same-origin',
    method: 'POST',
    headers: {
      'X-CSRFToken': Cookies.get('csrftoken'),
      'Accept': 'application/json',
      'Content-Type': 'application/json'
    }
  };
  if (body) {
    init.headers.body = body;
  }
  return fetch(url, init)
    .then(response => response.json());
}
