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
    this.days = [];
    this.costs = [];
    this.times = [];
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

      let month = this.startDate.getMonth();
      let year = this.startDate.getFullYear();

      let thisYear =  new Date().getFullYear();
      console.log(thisYear);
      let projectMonths = [];
      let monthlyCosts = [];
      let monthlyTimes = [];
      let cumulativeCosts = [];
      let cumulativeCost = 0;
      while (year <= thisYear) {

        while (month <= 12) {
          // let firstDayOfMonth = new Date(year, month);
          let monthlyCost = 0;
          let monthlyTime = 0;

          for (let i = 0; i < this.days.length, i++;) {

            if (days[i].getFullYear() == year && days[i].getMonth() == month) {
              monthlyCost = monthlyCost + this.costs[i];
              cumulativeCost = cumulativeCost + monthlyCost;
              monthlyTime = monthlyTime + this.times[i];
            }

          }

          projectMonths.push(month + ' ' + year);
          monthlyCosts.push(monthlyCost);
          monthlyTimes.push(monthlyTime);
          cumulativeCosts.push(cumulativeCost);
          month++;
        }


        console.log(year);
        console.log('one iteration');
        month = 1;
        year++;
      }
      // console.log(monthlyCosts);
      let monthlyCostTrace = this.getMonthTrace('Monthly Cost', projectMonths, monthlyCosts);
      // console.log('here');
      console.log(monthlyCostTrace);
      Plotly.newPlot(this.element, [monthlyCostTrace], {displaylogo: false});
      // console.log('not here');
    };

  }

  handleResponse(json) {

    // this.rawData = json.data;
    // this.initialStartDate = new Date(json.start_date);
    this.endDate = new Date(json.end_date);
    this.startDate = new Date(json.start_date);

    for (let value of json.data.days) {
      this.days.push(new Date(value))
    }

    // this.days = json.data.days;
    this.costs = json.data.costs;
    this.times = json.data.times;
    console.log(this.costs);

    // console.log(this.days);

    // let test = () => this.getMonthData();
    // test();
    this.getMonthData();

  }

  getMonthData() {

    month = this.startDate.getMonth();
    year = this.startDate.getFullYear();

    months = [];



    while (year <= new Date().getFullYear()) {

      console.log('one iteration');
      year++;
    }

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
