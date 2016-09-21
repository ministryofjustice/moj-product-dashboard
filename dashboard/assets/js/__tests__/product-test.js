jest.mock('../libs/plotly-custom');
import Plotly from '../libs/plotly-custom';

import {parseProductFinancials, getProductData} from '../libs/models';

const financial = {
  '2016-01': {
    'contractor': '100.500',
    'non-contractor': '200.80',
    'budget': '500.00',
    'additional': '50.2',
    'savings': '800.25'
  },
  '2016-02': {
    'contractor': '200.500',
    'non-contractor': '99.00',
    'budget': '800.00',
    'additional': '70.4',
    'savings': '0'
  },
  '2016-03': {
    'contractor': '150.500',
    'non-contractor': '149.20',
    'budget': '900.00',
    'additional': '10.2',
    'savings': '652.31'
  }
};

describe('parseProductFinancials', () => {
  it(`extracts and the converts the months and financial figures`, () => {
    const parsed = parseProductFinancials(financial);

    expect(Object.keys(parsed)).toEqual([ '2016-01', '2016-02', '2016-03' ]);
    expect(parsed['2016-01']).toEqual({
      budget: 500,
      total: 351.5,
      spendCumulative: 351.5,
      remaining: 148.5,
      savings: 800.25,
      savingsCumulative: 800.25
    });
    expect(parsed['2016-02']).toEqual({
      budget: 800,
      total: 369.9,
      spendCumulative: 721.4,
      remaining: 800 - 721.4,  // float is not exactly 78.6
      savings: 0,
      savingsCumulative: 800.25
    });
    expect(parsed['2016-03']).toEqual({
      budget: 900,
      total: 309.9,
      spendCumulative: 1031.3,
      remaining: 900 - 1031.3,  // float is not exactly 131.3
      savings: 652.31,
      savingsCumulative: 1452.56
    });
  });
});


describe('getProductData', () => {
  it(`uses the window.fetch from the ployfill`, () => {
    expect(window.fetch.polyfill).toBe(true);
  });

  it(`does a POST to the /product.json endpoint.
      when succeeds, returns a Promise with the product data`, () => {
    const data = {product: 'some data'};
    window.fetch = jest.fn().mockReturnValueOnce(
        new Promise((resolve, reject) => resolve({json: () => data})));
    return getProductData('product')
      .then(productData => {
        expect(window.fetch).toBeCalled();
        expect(productData).toEqual(data);
        const [url, init] = window.fetch.mock.calls[0];
        expect(url).toEqual('/product.json');
        expect(init.method).toEqual('POST');
      });
  });

  it(`when fails, throws an error`, () => {
    const error = {message: 'something went wrong'};
    window.fetch = jest.fn().mockReturnValueOnce(
        new Promise((resolve, reject) => reject(error)));
    return getProductData('product')
      .catch(err => {
        expect(window.fetch).toBeCalled();
        expect(err).toEqual(error);
        const [url, init] = window.fetch.mock.calls[0];
        expect(url).toEqual('/product.json');
        expect(init.method).toEqual('POST');
      });
  });
});
