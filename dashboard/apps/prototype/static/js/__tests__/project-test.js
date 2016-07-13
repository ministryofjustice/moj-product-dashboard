jest.mock('../plotly-custom');
import Plotly from '../plotly-custom';

import {parseProjectFinancials, getProjectData} from '../project';

const financial = {
  '2016-01': {
    'contractor': '100.500',
    'non-contractor': '200.80',
    'budget': '500.00',
    'additional': '50.2'
  },
  '2016-02': {
    'contractor': '200.500',
    'non-contractor': '100.20',
    'budget': '800.00',
    'additional': '70.4'
  },
  '2016-03': {
    'contractor': '150.500',
    'non-contractor': '150.20',
    'budget': '900.00',
    'additional': '10.2'
  }
};

describe('parseProjectFinancials', () => {
  it(`extracts and the converts the months and financial figures`, () => {
    const parsed = parseProjectFinancials(financial, '2016-02-10');

    expect(parsed.months).toEqual([ '2016-01', '2016-02', '2016-03' ]);
    expect(parsed.budget).toEqual([ 500, 800, 900 ]);

    expect(parsed.pastMonths).toEqual([ '2016-01' ]);
    expect(parsed.pastTotalCosts).toEqual([ 351.5 ]);
    expect(parsed.pastCumulative).toEqual([ 351.5 ]);
    expect(parsed.pastRemainings).toEqual([ 148.5 ]);

    expect(parsed.futureMonths).toEqual([ '2016-02', '2016-03' ]);
    expect(parsed.futureTotalCosts).toEqual([ 371.1, 310.9 ]);
    expect(parsed.futureCumulative).toEqual([ 722.6, 1033.5 ]);

  });
});


describe('getProjectData', () => {
  it(`uses the window.fetch from the ployfill`, () => {
    expect(window.fetch.polyfill).toBe(true);
  });

  it(`does a POST to the /project.json endpoint.
      when succeeds, returns a Promise with the project data`, () => {
    const data = {project: 'some data'};
    window.fetch = jest.fn().mockReturnValueOnce(
        new Promise((resolve, reject) => resolve({json: () => data})));
    return getProjectData()
      .then(projectData => {
        expect(window.fetch).toBeCalled();
        expect(projectData).toEqual(data);
        const [url, init] = window.fetch.mock.calls[0];
        expect(url).toEqual('/project.json');
        expect(init.method).toEqual('POST');
      });
  });

  it(`when fails, throws an error`, () => {
    const error = {message: 'something went wrong'};
    window.fetch = jest.fn().mockReturnValueOnce(
        new Promise((resolve, reject) => reject(error)));
    return getProjectData()
      .catch(err => {
        expect(window.fetch).toBeCalled();
        expect(err).toEqual(error);
        const [url, init] = window.fetch.mock.calls[0];
        expect(url).toEqual('/project.json');
        expect(init.method).toEqual('POST');
      });
  });
});
