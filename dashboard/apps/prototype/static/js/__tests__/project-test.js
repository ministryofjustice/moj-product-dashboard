jest.unmock('../project');

import * as project from '../project';

describe('parseProjectFinancials', () => {
  it('parses the month strings', () => {
    const financial = {'2016-01': {}, '2016-02': {}};
    const parsed = project.parseProjectFinancials(financial);
    expect(parsed.months).toEqual(['Jan 16', 'Feb 16']);
  });
});
