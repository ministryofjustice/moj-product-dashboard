jest.mock('../plotly-custom');
import Plotly from '../plotly-custom';

import {parseProjectFinancials, getProjectId, getProjectURL, plotProject,
        getProjectData} from '../project';

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
  it('extracts and the converts the months and financial figures', () => {
    const parsed = parseProjectFinancials(financial);
    expect(parsed.months).toEqual([ 'Jan 16', 'Feb 16', 'Mar 16' ]);
    expect(parsed.budget).toEqual([ 300, 300, 300 ]);
    expect(parsed.contractorCosts).toEqual([ 100.5, 200.5, 150.5 ]);
    expect(parsed.civilServantCosts).toEqual([ 200.8, 100.2, 150.2 ]);
    expect(parsed.additionalCosts).toEqual([ 50.2, 70.4, 10.2 ]);
    expect(parsed.totalCostsCumulative).toEqual([ 351.5, 722.6, 1033.5 ]);
  });
});


describe('getProjectId', () => {
  it('extracts the projectid from the query string of the url', () => {
    const projectid = getProjectId('http://127.0.0.1:8000/?projectid=51');
    expect(projectid).toEqual('51');
  });
});


describe('getProjectURL', () => {
  it('gets the project url based on the page url and project id', () => {
    const projectURL = getProjectURL('http://127.0.0.1:8000/?projectid=1', '50');
    expect(projectURL).toEqual('http://127.0.0.1:8000/?projectid=50');
  });
});


describe('plotProject', () => {
  it('calls the Plotly.newPlot function', () => {
    const elem = jest.fn();
    plotProject({financial}, elem);
    expect(Plotly.newPlot).toBeCalled();
  });
});


describe('getProjectData', () => {
  it('uses the window.fetch from the ployfill', () => {
    expect(window.fetch.polyfill).toBe(true);
  });
  it('does a POST to the /project.json endpoint', () => {
    window.fetch = jest.fn().mockImplementation(
        () => Promise.resolve({json: () => {}}));
    getProjectData('1', 'csrftoken');
    expect(window.fetch).toBeCalled();
    const [url, init] = window.fetch.mock.calls[0];
    expect(url).toEqual('/project.json');
    expect(init.method).toEqual('POST');
  });
});