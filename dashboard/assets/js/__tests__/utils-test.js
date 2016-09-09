import moment from 'moment';

import {
  monthRange,
  thisCalendarYear,
  lastCalendarYear,
  thisFinancialYear,
  lastFinancialYear,
  thisQuarter,
  lastQuarter,
  round,
  numberWithCommas
} from '../libs/utils';

describe('monthRange', () => {
  it(`returns the months between the startMonth and endMonth`, () => {
    expect(monthRange('2016-01', '2016-03', 'start'))
      .toEqual([ '2016-01-01', '2016-02-01', '2016-03-01' ]);

    expect(monthRange('2016-01', '2016-03', 'end'))
      .toEqual([ '2016-01-31', '2016-02-29', '2016-03-31' ]);

    expect(monthRange('2016-01', '2016-01', 'start'))
      .toEqual([ '2016-01-01' ]);

    expect(monthRange('2016-01', '2016-01', 'end'))
      .toEqual([ '2016-01-31' ]);

    expect(monthRange('2016-02', '2016-01', 'start'))
      .toEqual([ ]);

    expect(monthRange('2016-02', '2016-01', 'end'))
      .toEqual([ ]);
  });
});


describe('thisCalendarYear', () => {
  it(`gets the first day of this year as startDate
       and last day of this year as endDate`, () => {
    const {startDate, endDate} = thisCalendarYear(moment('2016-03-01'));
    expect(startDate).toEqual('2016-01-01');
    expect(endDate).toEqual('2016-12-31');
  });
});


describe('lastCalendarYear', () => {
  it(`gets the first day of last year as startDate
       and last day of last year as endDate`, () => {
    const {startDate, endDate} = lastCalendarYear(moment('2016-03-01'));
    expect(startDate).toEqual('2015-01-01');
    expect(endDate).toEqual('2015-12-31');
  });
});



describe('thisFinancialYear', () => {
  it(`gets the first day of this financial year as startDate
       and last day of this financial year as endDate`, () => {
    const fy1 = thisFinancialYear(moment('2016-03-01'));
    expect(fy1.startDate).toEqual('2015-04-01');
    expect(fy1.endDate).toEqual('2016-03-31');

    const fy2 = thisFinancialYear(moment('2016-04-02'));
    expect(fy2.startDate).toEqual('2016-04-01');
    expect(fy2.endDate).toEqual('2017-03-31');
  });
});


describe('lastFinancialYear', () => {
  it(`gets the first day of the last financial year as startDate
       and last day of the last financial year as endDate`, () => {
    const fy1 = lastFinancialYear(moment('2016-03-01'));
    expect(fy1.startDate).toEqual('2014-04-01');
    expect(fy1.endDate).toEqual('2015-03-31');

    const fy2 = lastFinancialYear(moment('2016-04-02'));
    expect(fy2.startDate).toEqual('2015-04-01');
    expect(fy2.endDate).toEqual('2016-03-31');
  });
});


describe('thisQuarter', () => {
  it(`gets the first day of this quarter as startDate
       and last day of this quarter as endDate`, () => {
    const q1 = thisQuarter(moment('2016-02-29'));
    expect(q1.startDate).toEqual('2016-01-01');
    expect(q1.endDate).toEqual('2016-03-31');

    const q2 = thisQuarter(moment('2016-04-12'));
    expect(q2.startDate).toEqual('2016-04-01');
    expect(q2.endDate).toEqual('2016-06-30');

    const q3 = thisQuarter(moment('2016-09-30'));
    expect(q3.startDate).toEqual('2016-07-01');
    expect(q3.endDate).toEqual('2016-09-30');

    const q4 = thisQuarter(moment('2016-10-01'));
    expect(q4.startDate).toEqual('2016-10-01');
    expect(q4.endDate).toEqual('2016-12-31');
  });
});



describe('lastQuarter', () => {
  it(`gets the first day of last quarter as startDate
       and last day of last quarter as endDate`, () => {
    const q1 = lastQuarter(moment('2016-02-29'));
    expect(q1.startDate).toEqual('2015-10-01');
    expect(q1.endDate).toEqual('2015-12-31');

    const q2 = lastQuarter(moment('2016-04-12'));
    expect(q2.startDate).toEqual('2016-01-01');
    expect(q2.endDate).toEqual('2016-03-31');

    const q3 = lastQuarter(moment('2016-09-30'));
    expect(q3.startDate).toEqual('2016-04-01');
    expect(q3.endDate).toEqual('2016-06-30');

    const q4 = lastQuarter(moment('2016-10-01'));
    expect(q4.startDate).toEqual('2016-07-01');
    expect(q4.endDate).toEqual('2016-09-30');
  });
});

describe('round', () => {
  it(`rounds the numbers and keeps the most significant parts`, () => {
    const pairs = [
      [1.23         , 1],         //  1
      [12.34        , 12],        //  12
      [123.45       , 123],       //  123
      [1234.56      , 1235],      //  1235
      [12345.67     , 12300],     //  12.3k
      [123456.78    , 123000],    //  123k
      [1234567.89   , 1230000],   //  1.23m
      [12345678.91  , 12350000],  //  12.35m
      [-12345678.91 , -12350000], // -12.35m
      [-1234567.89  , -1230000],  // -1.35m
      [-123456.78   , -123000],   // -123k
      [-12345.67    , -12300],    // -12.3k
      [-1234.56     , -1235],     // -1235
      [-123.45      , -123],      // -123
      [-12.34       , -12],       // -12
      [-1.23        , -1]         // -1
    ];
    pairs.map(([original, rounded]) => {
      expect(round(original)).toEqual(rounded);
    });
  });
});


describe('numberWithCommas', () => {
  it(`puts commas to separate every 3 digits of a number`, () => {
    const pairs = [
      ['123'   , '123'],
      [123     , '123'],
      [1234    , '1,234'],
      [12345   , '12,345'],
      [123456  , '123,456'],
      [1234567 , '1,234,567']
    ];
    pairs.map(([original, expected]) => {
      expect(numberWithCommas(original)).toEqual(expected);
    });
  });
});
