jest.mock('../plotly-custom');
import Plotly from '../plotly-custom';

import {parseProjectFinancials, plotProject, getProjectData} from '../project';

const financial = {
  '2016-01': {
    'contractor': '100.500',
    'non-contractor': '200.80',
    'budget': '300.00',
    'additional': '50.2'
  },
  '2016-02': {
    'contractor': '200.500',
    'non-contractor': '100.20',
    'budget': '300.00',
    'additional': '70.4'
  },
  '2016-03': {
    'contractor': '150.500',
    'non-contractor': '150.20',
    'budget': '300.00',
    'additional': '10.2'
  }
};

describe('parseProjectFinancials', () => {
  it(`extracts and the converts the months and financial figures`, () => {
    const parsed = parseProjectFinancials(financial);
    expect(parsed.months).toEqual([ 'Jan 16', 'Feb 16', 'Mar 16' ]);
    expect(parsed.budget).toEqual([ 300, 300, 300 ]);
    expect(parsed.contractorCosts).toEqual([ 100.5, 200.5, 150.5 ]);
    expect(parsed.civilServantCosts).toEqual([ 200.8, 100.2, 150.2 ]);
    expect(parsed.additionalCosts).toEqual([ 50.2, 70.4, 10.2 ]);
    expect(parsed.totalCostsCumulative).toEqual([ 351.5, 722.6, 1033.5 ]);
  });
});


describe('plotProject', () => {
  it(`calls the Plotly.newPlot function`, () => {
    const elem = jest.fn();
    plotProject({financial}, elem);
    expect(Plotly.newPlot).toBeCalled();
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
    return getProjectData('1', 'csrftoken')
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
    return getProjectData('2', 'csrftoken')
      .catch(err => {
        expect(window.fetch).toBeCalled();
        expect(err).toEqual(error);
        const [url, init] = window.fetch.mock.calls[0];
        expect(url).toEqual('/project.json');
        expect(init.method).toEqual('POST');
      });
  });
});
