import { postToBackend } from './utils';


export function initCommon() {
  const suncButton = document.getElementById('update-from-float');
  suncButton.addEventListener('click', function(event) {
    postToBackend('/sync.json');
    alert('Downloading latest float data.');
  });
}
