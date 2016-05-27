import 'whatwg-fetch';
import Cookies from 'js-cookie';
import Plotly from 'plotly.js/lib/core';
import * as bar from 'plotly.js/lib/bar';

Plotly.register([bar]);

class Figure {

  constructor(element) {
    this.element = element;
    this.data = {};
    this.layout = {};
  }

  plot() {
    Plotly.newPlot(this.element, this.data, this.layout, {displaylogo: false});
  }

  handleResponse(json) {
    this.data = json.data;
    this.layout = json.layout;
    this.plot();
  }

  getRequestFigure (url) {
    fetch(url)
      .then((response) => response.json())
      .then((json) => this.handleResponse(json));
  }

  postRequestFigure (url, requestJson) {
    fetch(url, {
      credentials: 'same-origin',
      method: 'POST',
      headers: {
        'X-CSRFToken': Cookies.get('csrftoken'),
        'Accept': 'application/json',
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(requestJson)
    })
    .then((response) => response.json())
      .then((json) => this.handleResponse(json));
  }

}

class ProjectCostFigure extends Figure {

  constructor(element) {
    super(element);
    this.data = {};
    this.initialEndDate = new Date();
    this.incrementLengths = ['day', 'week', 'month', 'year'];
    this.incrementLength = this.incrementLengths[3];
    this.startDate = undefined;


    this.getMonthTrace = (name, months, values) => {

      let costTrace = {
        name : name,
        x: months,
        y: values,
        type: 'bar'
      };

      return costTrace;

    };

    this.getMonthData = () => {

      let monthlyBreakdowns = this.getMonthsInProject();

      // console.log(projectMonths);

      for (let i = 0; i < monthlyBreakdowns.length; i++) {

        for (let j = 0; j < this.data.days.length; j++) {

          let date = new Date(this.data.days[j]);

          if (date.getMonth() == monthlyBreakdowns[i].monthNum && date.getFullYear() == monthlyBreakdowns[i].yearNum) {
            console.log('match');

            monthlyBreakdowns[i].monthCost += parseInt( this.data.costs[j] );
            monthlyBreakdowns[i].cumulCost += monthlyBreakdowns[i].monthCost;
            
            // projectMonths[i][2] = projectMonths[i][2] + parseInt( this.data.costs[j] );
            // projectMonths[i][3] = projectMonths[i][3] + projectMonths[i][2];
          }

        }
        console.log(monthlyBreakdowns[i].monthNum + ' ' + monthlyBreakdowns[i].yearNum + ' ' + monthlyBreakdowns[i].monthCost + ' ' + monthlyBreakdowns[i].cumulCost);

      }

      // let monthlyCostTrace = this.getMonthTrace('Monthly Cost', projectMonths, monthlyCosts);
      // console.log(monthlyCostTrace);
      // let traces = [];
      // traces[0] = monthlyCostTrace;
      // Plotly.newPlot(this.element, traces, {showlegend: false}, {displaylogo: false});
    };

  }

  getMonthsInProject() {

    let month = this.startDate.getMonth();
    let year = this.startDate.getFullYear();
    let thisYear = new Date().getFullYear();
    let monthlyBreakdowns = [];

    for (year; year <= thisYear; year++) {

      for (month; month <= 12; month++) {

        monthlyBreakdowns.push({
            monthNum: month,
            yearNum: year,
            monthCost: 0,
            cumulCost: 0,
            monthTimeSpent: 0
          });

      }
      month = 1;
    }
    return monthlyBreakdowns;
  }

  handleResponse(json) {

    this.endDate = new Date(json.end_date);
    this.startDate = new Date(json.start_date);

    this.data = json.data;
    console.log(this.data);
    this.getMonthData();

  }

}

var testRequest = {

  requested_figure : 'staff_split',

  projects : ['Digital'],

  persons : [],

  areas : [],

  start_date: '2015-01-01',

  end_date: '2016-05-23'

};

var projectTestRequest = {

  requested_figure : 'project_cost',

  projects : ['CLA Public'],

  persons : [],

  areas : [],

  start_date: '2015-01-01',

  end_date: '2016-05-23'

};


//Run on page load
function onLoad() {
  const figA = document.getElementById('fig-a');
  const figB = document.getElementById('fig-b');
  const figC = document.getElementById('fig-c');
  const figD = document.getElementById('fig-d');

  const fA = new Figure(figA);
  const fB = new Figure(figB);
  const fC = new ProjectCostFigure(figC);
  const fD = new Figure(figD);

  fA.getRequestFigure('/comp/');
  fB.postRequestFigure('/getfig/', testRequest);
  fC.postRequestFigure('/getfig/', projectTestRequest);
  fD.getRequestFigure('/getrand/');
}

document.addEventListener("DOMContentLoaded", () => onLoad());
