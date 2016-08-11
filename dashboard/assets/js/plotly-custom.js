// only take the bits from plotly used by the application
// https://plot.ly/javascript/modularizing-monolithic-javascript-projects
import Plotly from 'plotly.js/lib/core';
import * as bar from 'plotly.js/lib/bar';
Plotly.register([bar]);

export default Plotly;
