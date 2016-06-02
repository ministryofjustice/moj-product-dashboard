import 'whatwg-fetch';
import Cookies from 'js-cookie';
import Plotly from 'plotly.js/lib/core';
import * as bar from 'plotly.js/lib/bar';
Plotly.register([bar]);

import $ from 'jquery';
import select2 from 'select2';
import URI from 'urijs';

require('select2/dist/css/select2.min.css');
require('../styles/gov-uk-elements.css');
require('../styles/main.css');


class Figure {

  constructor(element) {
    // if (new.target === Figure) {
    //   throw new TypeError("Figure class is abstract and should not be instantiated");
    // }
    this.element = element;
    this.data = {};
  }

  plot() {
    // Override this
  }

  handleResponse(json) {
    this.data = json;
    console.log(this.data)
  }

  getRequestFigure (url) {
    fetch(url)
      .then((response) => response.json())
      .then((json) => this.handleResponse(json));
  }

  postRequestFigure (url, requestJson) {
    // console.log(requestJson);
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


class SingleProjectFigure extends Figure {



}


class MonthCostFigure extends Figure {

  constructor(element) {
    super(element);
    this.incrementLengths = ['day', 'week', 'month', 'year'];
    this.startDate = undefined;
    this.monthNames = ['','Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];

    this.getMonthData = () => {

      let monthlyBreakdowns = this.getMonthsInProject();

      monthlyBreakdowns = this.calcMonthlyData(monthlyBreakdowns);

      let monthCostTrace = [this.makeMonthlyTrace(monthlyBreakdowns, 'monthCost', 'Monthly Cost', 'bar')];

      Plotly.newPlot(this.element, monthCostTrace, {displaylogo: false});

    };

  }


  makeSplitTraces(monthlyBreakdowns) {
    let x_axis = [];
    let cs_y_axis = [];
    let contr_y_axis = [];

    for (let month of monthlyBreakdowns) {

      let cs_perc = 0;
      let contr_perc = 0;

      x_axis.push(this.monthNames[month.monthNum] + ' ' + month.yearNum);

      if (month.monthCsProp != 0) { cs_perc = month.monthCsProp / (month.monthCsProp + month.monthContProp) }
      if (month.monthCsProp != 0) { contr_perc = month.monthContProp / (month.monthContProp + month.monthCsProp) }

      cs_y_axis.push(cs_perc);
      contr_y_axis.push(contr_perc);

      let cs_trace = {x: x_axis, y: cs_y_axis, type: 'bar'};
      let contr_trace = {x: x_axis, y: contr_y_axis, type: 'bar'};

      let traces = [cs_trace, contr_trace];

      return traces;

    }

  }

  makeMonthlyTrace(monthlyBreakdowns, y_series, name, type) {

    let x_axis = [];
    let y_axis = [];

    for (let month of monthlyBreakdowns) {

      x_axis.push(this.monthNames[month.monthNum] + ' ' + month.yearNum);
      y_axis.push(month[y_series]);

    }

    let trace = {
      x: x_axis,
      y: y_axis,
      name: name,
      type: type
    };
    return trace
  }

  makeCumulTrace(monthlyBreakdowns) {

    let x_axis = [];
    let y_axis = [];
    let cumulCost = 0;
    for (let month of monthlyBreakdowns) {
      cumulCost += month.monthCost;

      x_axis.push(this.monthNames[month.monthNum] + ' ' + month.yearNum);
      y_axis.push(cumulCost);

    }

    let trace = {
      x: x_axis,
      y: y_axis,
      name: name,
      mode: 'lines'
    };
    return trace
  }

  calcMonthlyData(monthlyBreakdowns) {

    for (let i = 0; i < monthlyBreakdowns.length; i++) {

        for (let j = 0; j < this.data.active_days.length; j++) {

          let date = new Date(this.data.active_days[j].date);

          if (date.getMonth() == monthlyBreakdowns[i].monthNum && date.getFullYear() == monthlyBreakdowns[i].yearNum) {
            // console.log('>>>>' + date.getMonth() + date.yearNum());

            monthlyBreakdowns[i].monthCost += parseInt( this.data.active_days[j].cost );
            // Is this where I'm going wrong on the cumulative cost?
            monthlyBreakdowns[i].cumulCost += monthlyBreakdowns[i].monthCost;
            monthlyBreakdowns[i].monthCsProp += parseInt( this.data.active_days[j].cs_perc );
            monthlyBreakdowns[i].monthContProp += parseInt( this.data.active_days[j].contr_perc );
          }

        }
    }
    console.log(monthlyBreakdowns);
    return monthlyBreakdowns;

  }

  getMonthsInProject() {

    let month = this.startDate.getMonth();
    let year = this.startDate.getFullYear();
    let thisYear = new Date().getFullYear();
    let monthlyBreakdowns = [];

    for (year; year <= thisYear; year++) {

      for (month; month <= 12; month++) {

        if (year == 2016 && month == 4) {break;}

        monthlyBreakdowns.push({
            monthNum: month,
            yearNum: year,
            monthCost: 0,
            cumulCost: 0,
            monthTimeSpent: 0,
            monthCsProp: 0,
            monthContProp: 0
          });

      }
      month = 1;
    }
    // console.log(monthlyBreakdowns);
    return monthlyBreakdowns;
  }

  handleResponse(json) {

    this.startDate = new Date(json.start_date);

    this.data = json;
    // console.log(this.data);
    this.getMonthData();

  }

}

class MonthCumulFigure extends Figure {

  constructor(element) {
    super(element);
    this.incrementLengths = ['day', 'week', 'month', 'year'];
    this.startDate = undefined;
    this.monthNames = ['','Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];

    this.getMonthData = () => {

      let monthlyBreakdowns = this.getMonthsInProject();

      monthlyBreakdowns = this.calcMonthlyData(monthlyBreakdowns);

      let cumulCostTrace = [this.makeCumulTrace(monthlyBreakdowns)];

      Plotly.newPlot(this.element, cumulCostTrace, {displaylogo: false});

    };

  }


  makeSplitTraces(monthlyBreakdowns) {
    let x_axis = [];
    let cs_y_axis = [];
    let contr_y_axis = [];

    for (let month of monthlyBreakdowns) {

      let cs_perc = 0;
      let contr_perc = 0;

      x_axis.push(this.monthNames[month.monthNum] + ' ' + month.yearNum);

      if (month.monthCsProp != 0) { cs_perc = month.monthCsProp / (month.monthCsProp + month.monthContProp) }
      if (month.monthCsProp != 0) { contr_perc = month.monthContProp / (month.monthContProp + month.monthCsProp) }

      cs_y_axis.push(cs_perc);
      contr_y_axis.push(contr_perc);

      let cs_trace = {x: x_axis, y: cs_y_axis, type: 'bar'};
      let contr_trace = {x: x_axis, y: contr_y_axis, type: 'bar'};

      let traces = [cs_trace, contr_trace];

      return traces;

    }

  }

  makeMonthlyTrace(monthlyBreakdowns, y_series, name, type) {

    let x_axis = [];
    let y_axis = [];

    for (let month of monthlyBreakdowns) {

      x_axis.push(this.monthNames[month.monthNum] + ' ' + month.yearNum);
      y_axis.push(month[y_series]);

    }

    let trace = {
      x: x_axis,
      y: y_axis,
      name: name,
      type: type
    };
    return trace
  }

  makeCumulTrace(monthlyBreakdowns) {

    let x_axis = [];
    let y_axis = [];
    let cumulCost = 0;
    for (let month of monthlyBreakdowns) {
      cumulCost += month.monthCost;

      x_axis.push(this.monthNames[month.monthNum] + ' ' + month.yearNum);
      y_axis.push(cumulCost);

    }

    let trace = {
      x: x_axis,
      y: y_axis,
      name: name,
      mode: 'lines'
    };
    return trace
  }

  calcMonthlyData(monthlyBreakdowns) {

    for (let i = 0; i < monthlyBreakdowns.length; i++) {

      for (let j = 0; j < this.data.active_days.length; j++) {

        let date = new Date(this.data.active_days[j].date);

        if (date.getMonth() == monthlyBreakdowns[i].monthNum && date.getFullYear() == monthlyBreakdowns[i].yearNum) {
          // console.log('>>>>' + date.getMonth() + date.yearNum());

          monthlyBreakdowns[i].monthCost += parseInt( this.data.active_days[j].cost );
          // Is this where I'm going wrong on the cumulative cost?
          monthlyBreakdowns[i].cumulCost += monthlyBreakdowns[i].monthCost;
          monthlyBreakdowns[i].monthCsProp += parseInt( this.data.active_days[j].cs_perc );
          monthlyBreakdowns[i].monthContProp += parseInt( this.data.active_days[j].contr_perc );
        }

      }
    }
    console.log(monthlyBreakdowns);
    return monthlyBreakdowns;

  }

  getMonthsInProject() {

    let month = this.startDate.getMonth();
    let year = this.startDate.getFullYear();
    let thisYear = new Date().getFullYear();
    let monthlyBreakdowns = [];

    for (year; year <= thisYear; year++) {

      for (month; month <= 12; month++) {

        if (year == 2016 && month == 4) {break;}

        monthlyBreakdowns.push({
          monthNum: month,
          yearNum: year,
          monthCost: 0,
          cumulCost: 0,
          monthTimeSpent: 0,
          monthCsProp: 0,
          monthContProp: 0
        });

      }
      month = 1;
    }
    // console.log(monthlyBreakdowns);
    return monthlyBreakdowns;
  }

  handleResponse(json) {

    this.startDate = new Date(json.start_date);

    this.data = json;
    // console.log(this.data);
    this.getMonthData();

  }

}

class StaffSplitFigure extends Figure {

  constructor(element) {
    super(element);
    this.incrementLengths = ['day', 'week', 'month', 'year'];
    this.startDate = undefined;
    this.monthNames = ['','Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];

    this.getMonthData = () => {

      let monthlyBreakdowns = this.getMonthsInProject();

      monthlyBreakdowns = this.calcMonthlyData(monthlyBreakdowns);

      let staffSplitTrace = this.makeSplitTraces(monthlyBreakdowns, 'monthCost', 'Monthly Cost', 'bar');

      Plotly.newPlot(this.element, staffSplitTrace, {displaylogo: false, barmode: 'stack'});

    };

  }


  makeSplitTraces(monthlyBreakdowns) {
    let x_axis = [];
    let cs_y_axis = [];
    let contr_y_axis = [];
    // let traces = [];

    for (let month of monthlyBreakdowns) {

      let cs_perc = 0;
      let contr_perc = 0;

      x_axis.push(this.monthNames[month.monthNum] + ' ' + month.yearNum);

      if (month.monthCsProp != 0) { cs_perc = month.monthCsProp / (month.monthCsProp + month.monthContProp)  }
      if (month.monthContProp != 0) { contr_perc = month.monthContProp / (month.monthContProp + month.monthCsProp)  }

      cs_y_axis.push(cs_perc);
      contr_y_axis.push(contr_perc);

      console.log(cs_perc);
      console.log(contr_perc);

    }
    let cs_trace = {x: x_axis, y: cs_y_axis, type: 'bar'};
    let contr_trace = {x: x_axis, y: contr_y_axis, type: 'bar'};

    console.log(cs_trace);
    console.log(contr_trace);

    let traces = [cs_trace, contr_trace];

    return traces;


  }

  makeMonthlyTrace(monthlyBreakdowns, y_series, name, type) {

    let x_axis = [];
    let y_axis = [];

    for (let month of monthlyBreakdowns) {

      x_axis.push(this.monthNames[month.monthNum] + ' ' + month.yearNum);
      y_axis.push(month[y_series]);

    }

    let trace = {
      x: x_axis,
      y: y_axis,
      name: name,
      type: type
    };
    return trace;
  }

  makeCumulTrace(monthlyBreakdowns) {

    let x_axis = [];
    let y_axis = [];
    let cumulCost = 0;
    for (let month of monthlyBreakdowns) {
      cumulCost += month.monthCost;

      x_axis.push(this.monthNames[month.monthNum] + ' ' + month.yearNum);
      y_axis.push(cumulCost);

    }

    let trace = {
      x: x_axis,
      y: y_axis,
      name: name,
      mode: 'lines'
    };
    return trace
  }

  calcMonthlyData(monthlyBreakdowns) {

    for (let i = 0; i < monthlyBreakdowns.length; i++) {

      for (let j = 0; j < this.data.active_days.length; j++) {

        let date = new Date(this.data.active_days[j].date);

        if (date.getMonth() == monthlyBreakdowns[i].monthNum && date.getFullYear() == monthlyBreakdowns[i].yearNum) {
          // console.log('>>>>' + date.getMonth() + date.yearNum());

          monthlyBreakdowns[i].monthCost += parseInt( this.data.active_days[j].cost );
          // Is this where I'm going wrong on the cumulative cost?
          monthlyBreakdowns[i].cumulCost += monthlyBreakdowns[i].monthCost;
          monthlyBreakdowns[i].monthCsProp += parseInt( this.data.active_days[j].cs_perc );
          monthlyBreakdowns[i].monthContProp += parseInt( this.data.active_days[j].contr_perc );
        }

      }
    }
    console.log(monthlyBreakdowns);
    return monthlyBreakdowns;

  }

  getMonthsInProject() {

    let month = this.startDate.getMonth();
    let year = this.startDate.getFullYear();
    let thisYear = new Date().getFullYear();
    let monthlyBreakdowns = [];

    for (year; year <= thisYear; year++) {

      for (month; month <= 12; month++) {

        if (year == 2016 && month == 4) {break;}

        monthlyBreakdowns.push({
          monthNum: month,
          yearNum: year,
          monthCost: 0,
          cumulCost: 0,
          monthTimeSpent: 0,
          monthCsProp: 0,
          monthContProp: 0
        });

      }
      month = 1;
    }
    // console.log(monthlyBreakdowns);
    return monthlyBreakdowns;
  }

  handleResponse(json) {

    this.startDate = new Date(json.start_date);

    this.data = json;
    // console.log(this.data);
    this.getMonthData();

  }

}



var testRequest = {
  requested_figure : 'staff_split',
  projectids : [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
  persons : [],
  areas : [],
  start_date: '2015-01-01',
  end_date: '2016-05-23'
};


var projectTestRequest = {

  request_type : 'single_project',
  project_id : 52,
  start_date: '2015-01-01',
  end_date: '2016-06-01',
  time_increment: 'day'

};


function plot() {

  const figA = document.getElementById('fig-a');
  const figB = document.getElementById('fig-b');
  const figC = document.getElementById('fig-c');

  const fA = new Figure(figA);
  // const fB = new MonthCumulFigure(figB);
  // const fC = new StaffSplitFigure(figC);

  // console.log(document.getElementById('projects').value);

  // fA.postRequestFigure('/getdata/', projectTestRequest);
  // fB.postRequestFigure('/getdata/', projectTestRequest);
  // fC.postRequestFigure('/getdata/', projectTestRequest);

  fA.postRequestFigure('/getdata/', projectTestRequest)

}


/**
 * get projectId based on the query string
 */
function getProjectId() {
  const projectId = URI(window.location.href).query(true).projectid;
  console.log('projectId:', projectId);
  return projectId;
};


function loadProject(id) {
  const url = [location.protocol, '//', location.host, location.pathname].join('');

  window.location.href = url + '?projectid=' + id;
};



$(() => {
  const projectId = getProjectId();
  // plot project
  plot();
  // dropdown project selector
  $('#projects').select2().on("select2:select", (e) => {
    loadProject(e.params.data.id);
  });
})
