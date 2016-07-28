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
    'non-contractor': '99.00',
    'budget': '800.00',
    'additional': '70.4'
  },
  '2016-03': {
    'contractor': '150.500',
    'non-contractor': '149.20',
    'budget': '900.00',
    'additional': '10.2'
  }
};

describe('parseProjectFinancials', () => {
  it(`extracts and the converts the months and financial figures`, () => {
    const parsed = parseProjectFinancials(financial);

    expect(Object.keys(parsed)).toEqual([ '2016-01', '2016-02', '2016-03' ]);
    expect(parsed['2016-01']).toEqual({
      budget: 500,
      total: 351.5,
      cumulative: 351.5,
      remaining: 148.5
    });
    expect(parsed['2016-02']).toEqual({
      budget: 800,
      total: 369.9,
      cumulative: 721.4,
      remaining: 800 - 721.4  // float is not exactly 78.6
    });
    expect(parsed['2016-03']).toEqual({
      budget: 900,
      total: 309.9,
      cumulative: 1031.3,
      remaining: 900 - 1031.3  // float is not exactly 131.3
    });
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
    return getProjectData('project')
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
    return getProjectData('project')
      .catch(err => {
        expect(window.fetch).toBeCalled();
        expect(err).toEqual(error);
        const [url, init] = window.fetch.mock.calls[0];
        expect(url).toEqual('/project.json');
        expect(init.method).toEqual('POST');
      });
  });
});
