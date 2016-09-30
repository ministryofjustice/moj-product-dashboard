import moment from 'moment';
import React, { Component } from 'react';
import { Product, statusMapping } from '../libs/models';
import { numberWithCommas } from '../libs/utils';
import { ExternalLinkExtra } from '../components/product-table';


export class ProductInfo extends Component {

  dateInEnglish(date) {
    return moment(date, 'YYYY-MM-DD').format('Do MMM YYYY');
  }

  dateInNum(date) {
    if (date === null) {
      return '-';
    }
    return moment(date, 'YYYY-MM-DD').format('DD/MM/YYYY');
  }

  Status() {
    const { status, reason }= this.props.product.status;
    const date = this.props.product.status['start_date'];
    let className = 'bold-xlarge';
    if (status in statusMapping) {
      className = `${className}  status-text ${statusMapping[status]}-inverse`;
    }
    return (
      <div>
        <h3 className="heading-small">Product status</h3>
        <div className="banner">
          <span className={ className }>{ status || '-' }</span>
        </div>
        <p className="font-small">{ reason }</p>
        <p className="font-small">{ date ? `Last updated ${this.dateInNum(date)}` : null }</p>
      </div>
    );
  }

  PhaseDates() {
    const { discoveryStart, alphaStart,
            betaStart, liveStart, endDate } = this.props.product;
    return (
      <div>
        <div className="grid-row">
          <div className="column-one-quarter">
            <p className="heading-small">Discovery start</p>
            <p className="font-small">{ discoveryStart ? this.dateInEnglish(discoveryStart) : '-' }</p>
          </div>
          <div className="column-one-quarter">
            <p className="heading-small">Alpha start</p>
            <p className="font-small">{ alphaStart ? this.dateInEnglish(alphaStart) : '-' }</p>
          </div>
          <div className="column-one-quarter">
            <p className="heading-small">Beta start</p>
            <p className="font-small">{ betaStart ? this.dateInEnglish(betaStart) : '-' }</p>
          </div>
          <div className="column-one-quarter">
            <p className="heading-small">Live start</p>
            <p className="font-small">{ liveStart? this.dateInEnglish(liveStart) : '-' }</p>
          </div>
        </div>
        <div className="grid-row">
          <div className="column-one-quarter">
            <p className="heading-small">End date</p>
            <p className="font-small">{ endDate ? this.dateInEnglish(endDate) : '-' }</p>
          </div>
        </div>
      </div>
    );
  }

  Recurring(costs) {
    const sortedCosts = costs.sort(Product.compareDate('start_date', 'desc'));
    const Rows = () => {
      if (sortedCosts.length == 0) {
        return (
          <tr>
            <td>-</td>
            <td className="numeric">-</td>
            <td className="numeric">-</td>
            <td className="numeric">-</td>
          </tr>
        );
      }
      return (
        sortedCosts.map(cost => {
          const unit = {'Monthly' : 'month', 'Annually': 'year'}[cost.freq];
          return (
           <tr key={cost.id}>
             <td>{ cost.name || '' }</td>
             <td className="numeric">{ `\u00a3${numberWithCommas(cost.cost | 0)}/${unit}` }</td>
             <td className="numeric">{ this.dateInNum(cost['start_date']) }</td>
             <td className="numeric">{ this.dateInNum(cost['end_date']) }</td>
           </tr>
          )
        }
        )
      );
    }

    return (
      <tbody>
        <tr>
          <th scope="col">Recurring</th>
          <th className="numeric" scope="col">Amount</th>
          <th className="numeric" scope="col">Start Date</th>
          <th className="numeric" scope="col">End Date</th>
        </tr>
        { Rows() }
      </tbody>
    );
  }

  OneOff(costs) {
    const sortedCosts = costs.sort(Product.compareDate('start_date', 'desc'));
    const Rows = () => {
      if (sortedCosts.length == 0) {
        return (
          <tr>
            <td>-</td>
            <td className="numeric">-</td>
            <td className="numeric">-</td>
            <td className="numeric"></td>
          </tr>
        );
      }
      return (
        sortedCosts.map(cost => (
          <tr key={cost.id}>
            <td>{ cost.name || '' }</td>
            <td className="numeric">{ `\u00a3${numberWithCommas(cost.cost | 0)}` }</td>
            <td className="numeric">{ this.dateInNum(cost['start_date']) }</td>
            <td className="numeric"></td>
          </tr>
          )
        )
      );
    }

    return (
      <tbody>
        <tr>
          <th scope="col">One off</th>
          <th className="numeric" scope="col">Amount</th>
          <th className="numeric" scope="col">Date</th>
          <th className="numeric" scope="col"></th>
        </tr>
        { Rows() }
      </tbody>
    );
  }

  Budgets() {
    const budgets = this.props.product.budgets
      .sort(Product.compareDate('date', 'desc'));
    if (budgets.length == 0) {
      return (<p className="font-small">-</p>);
    }
    return (
      <ul style={{marginTop: '20px'}}>
      {
        budgets.map(budget => (
          <li key={budget.date}>
            <span className="heading-small">
              { `Set on ${ this.dateInEnglish(budget.date) }` }
            </span>
            <br/>
            <span>
              {`\u00a3${numberWithCommas(budget.budget | 0)}`}
            </span>
          </li>
          )
        )
      }
      </ul>
    );
  }

  Team() {
    const { serviceManager, productManager, deliveryManager, serviceArea } = this.props.product;
    return (
      <div className="grid-row">
        <div className="column-one-quarter">
            <p className="heading-small">Service manager</p>
            <p className="font-small">{ serviceManager || '-' }</p>
        </div>
        <div className="column-one-quarter">
            <p className="heading-small">Product manager</p>
            <p className="font-small">{ productManager || '-' }</p>
        </div>
        <div className="column-one-quarter">
            <p className="heading-small">Delivery manager</p>
            <p className="font-small">{ deliveryManager || '-' }</p>
        </div>
        <div className="column-one-quarter">
            <p className="heading-small">Service area</p>
            <p className="font-small">{ serviceArea || '-' }</p>
        </div>
      </div>
    );
  }

  LinkNote(link) {
    if (link.note) {
      return (
         <span className="external-link-note">{ link.note }</span>
      )
    }
  }

  Links(links) {
    if (links.length > 0) {
      return (
        <div>
          <h3 className="heading-small">External links</h3>
          <ul className="external-links">
          {
            links.map((link, index) => (
              <li key={index} className={ link.type }>
                <a className={ link.type } href={ link.url } rel="external" target="_blank">
                  { link.name }
                </a>{ this.LinkNote(link) }
                <ExternalLinkExtra baseURL={ link.url } />
              </li>
            ))
          }
          </ul>
        </div>
      )
    }
  }

  render() {
    return (
      <div id="product-info">
        { this.Status() }
        <h3 className="heading-small">Product description</h3>
        <p className="font-small">{ this.props.product.description || '-' }</p>
        <h3 className="heading-small">Phase dates</h3>
        { this.PhaseDates() }
        <h3 className="heading-small">Team description</h3>
        { this.Team() }
        <h3 className="heading-small">Budget</h3>
        { this.Budgets() }
        <h3 className="heading-small">Costs</h3>
        <table>
          { this.Recurring(this.props.product.recurringCosts) }
          { this.OneOff(this.props.product.oneOffCosts) }
        </table>
        <h3 className="heading-small">Savings enabled</h3>
        <table>
          { this.Recurring(this.props.product.recurringSavings) }
          { this.OneOff(this.props.product.oneOffSavings) }
        </table>
        { this.Links(this.props.product['links']) }
      </div>
    );
  }
}

ProductInfo.propTypes = {
  product: React.PropTypes.instanceOf(Product).isRequired
}
