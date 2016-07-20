import Cookies from 'js-cookie';
import moment from 'moment';

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

/**
 * get an array of month between the startMonth
 * and endMonth.
 * */
export function monthRange(startDate, endDate, startOrEnd) {
  let start, end;
  if (startOrEnd == 'start') {
    start = moment(startDate).startOf('month');
    end = moment(endDate).startOf('month');
  } else {
    start = moment(startDate).endOf('month');
    end = moment(endDate).endOf('month');
  };
  const range = [];
  let month = start;
  while (month <= end) {
    range.push(month.format('YYYY-MM-DD'));
    if (startOrEnd == 'start') {
      month = month.add(1, 'months').startOf('month');
    } else {
      month = month.add(1, 'months').endOf('month');
    }
  }
  return range;
}


/**
 * strip off day from date
 **/
export function stripOffDay(date) {
  return moment(date, 'YYYY-MM-DD').format('YYYY-MM');
}


/**
 * gets the first day of this year as startDate
 * and last day of this year as endDate
 **/
export function thisCalendarYear(now) {
  const year = moment(now).year();
  const startDate = moment(`${year}-01-01`).format('YYYY-MM-DD');
  const endDate = moment(`${year}-12-31`).format('YYYY-MM-DD');
  return {startDate, endDate};
}


/**
 * gets the first day of the last year as startDate
 * and last day of the last year as endDate
 **/
export function lastCalendarYear(now) {
  const year = moment(now).year() - 1;
  const startDate = moment(`${year}-01-01`).format('YYYY-MM-DD');
  const endDate = moment(`${year}-12-31`).format('YYYY-MM-DD');
  return {startDate, endDate};
}


/**
 * gets the first day of the current financial year as startDate
 * and last day of the current financial year as endDate
 **/
export function thisFinancialYear(now) {
  const year = moment(now).year();
  let financialYear;
  if (moment(now) > moment(`${year}-04-01`)) {
    financialYear = year;
  } else {
    financialYear = year -1;
  }
  const startDate = moment(`${financialYear}-04-01`).format('YYYY-MM-DD');
  const endDate = moment(`${financialYear + 1}-03-31`).format('YYYY-MM-DD');
  return {startDate, endDate};
}


/**
 * gets the first day of the last financial year as startDate
 * and last day of the last financial year as endDate
 **/
export function lastFinancialYear(now) {
  const lastYearToday = moment(now).subtract(1, 'years');
  const year = lastYearToday.year();
  let financialYear;
  if (lastYearToday > moment(`${year}-04-01`)) {
    financialYear = year;
  } else {
    financialYear = year -1;
  }
  const startDate = moment(`${financialYear}-04-01`).format('YYYY-MM-DD');
  const endDate = moment(`${financialYear + 1}-03-31`).format('YYYY-MM-DD');
  return {startDate, endDate};
}


/**
 * gets the first day of the this quarter as startDate
 * and last day of the this quarter as endDate
 **/
export function thisQuarter(now) {
  const month = moment(now).month();
  const year = moment(now).year();
  if (0 <= month && month <= 2) {
    return {
      startDate: moment(`${year}-01-01`).format('YYYY-MM-DD'),
      endDate: moment(`${year}-03-31`).format('YYYY-MM-DD')
    };
  };
  if (3 <= month && month <= 5) {
    return {
      startDate: moment(`${year}-04-01`).format('YYYY-MM-DD'),
      endDate: moment(`${year}-06-30`).format('YYYY-MM-DD')
    };
  };
  if (6 <= month && month <= 8) {
    return {
      startDate: moment(`${year}-07-01`).format('YYYY-MM-DD'),
      endDate: moment(`${year}-09-30`).format('YYYY-MM-DD')
    };
  };
  return {
    startDate: moment(`${year}-10-01`).format('YYYY-MM-DD'),
    endDate: moment(`${year}-12-31`).format('YYYY-MM-DD')
  };
}


export function lastQuarter(now) {
  const threeMonthAgo = moment(now).subtract(3, 'months');
  return thisQuarter(threeMonthAgo);
}


export function startOfMonth(date) {
  return moment(date).startOf('month').format('YYYY-MM-DD');
}


export function endOfMonth(date) {
  return moment(date).endOf('month').format('YYYY-MM-DD');
}


export function min(items) {
  return items.reduce((x, y) => x < y ? x : y)
}


export function max(items) {
  return items.reduce((x, y) => x > y ? x : y)
}

export function round(num) {
  const isNegative = num < 0;
  const K = 1000;
  num = Math.abs(num);
  if ( num < 10 * K ) {
    // 1234-> 1234
    num = Math.round(num);
  } else if ( num < 100 * K ) {
    // 12345 -> 12.3k
    num = Math.round(num / 100) * 100;
  } else if ( num < 1000 * K ) {
    // 123456 -> 123k
    num = Math.round(num / 1000) * 1000;
  } else {
    // 1234567 -> 1.23m
    num = Math.round(num / 10000) * 10000;
  };
  return isNegative ? -num : num;
}
