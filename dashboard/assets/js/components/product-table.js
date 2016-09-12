import moment from 'moment';
import React, { Component } from 'react';
import Griddle from 'griddle-react';

import { statusMapping } from '../libs/models';
import { numberWithCommas } from '../libs/utils';

import RedImg from '../../img/red.png';
import AmberImg from '../../img/amber.png';
import GreenImg from '../../img/green.png';


const FilterComponent = ({ changeFilter }) => (
  <div className="filter-container">
    <label className="form-label" htmlFor="filter-results">
      Filter results
    </label>
    <input
      type="text"
      id="filter-results"
      name="filter"
      className="form-control"
      onChange={(e) => changeFilter(e.target.value)}
    />
  </div>
);

/**
 * React component for a table of products
 */
export const ProductTable = ({ projects, showService, showFilter }) => {

  const displayMoney = (props) => {
    const number = numberWithCommas(Number(props.data).toFixed(0));
    return (<span>£{number}</span>);
  };

  const columnMetadata = [
    {
      'columnName': 'name',
      'order': 1,
      'displayName': 'Product',
      'customComponent': (props) => {
        let url;
        if (props.rowData.type == 'ProjectGroup') {
          url = `/project-groups/${props.rowData.id}`;
        } else {
          url = `/projects/${props.rowData.id}`;
        };
        return (<a href={url}>{props.data}</a>);
      },
    },
    {
      'columnName': 'phase',
      'order': 3,
      'displayName': 'Phase',
      'customComponent': (props) => {
        const val = props.data === 'Not Defined' ? '' : props.data;
        return (<span>{val}</span>);
      },
      'customCompareFn': (phase) => {
        const val = {Discovery: 0, Alpha: 1, Beta: 2, Live: 3, Ended: 4}[phase];
        return typeof val === 'undefined' ? 5 : val;
      },
    },
    {
      'columnName': 'status',
      'order': 4,
      'displayName': 'Status',
      'customComponent': (props) => {
        if (props.data in statusMapping) {
          return (
            <strong className={statusMapping[props.data]}>{props.data}</strong>
          );
        };
        return null;
      }
    },
    {
      'columnName': 'current_fte',
      'order': 5,
      'displayName': 'Current FTE',
      'customCompareFn': Number,
      'customComponent': (props) => (
        <span>
          {Number(props.data).toFixed(1)}
        </span>),
    },
    {
      'columnName': 'cost_to_date',
      'order': 6,
      'displayName': 'Cost to date',
      'customCompareFn': Number,
      'customComponent': displayMoney,
      'cssClassName': 'money-value'
    },
    {
      'columnName': 'budget',
      'order': 7,
      'displayName': 'Budget',
      'customCompareFn': Number,
      'customComponent': displayMoney,
      'cssClassName': 'money-value'
    },
    {
      'columnName': 'financial_rag',
      'order': 8,
      'displayName': 'Financial RAG',
      'customCompareFn': (label) => {
        const mappings = {RED: 3, AMBER: 2, GREEN: 1};
        return mappings[label];
      },
      'customComponent': (props) => {
        const mapping = { RED: RedImg, AMBER: AmberImg, GREEN: GreenImg };
        return (
            <img src={ mapping[props.data] } className="rag" alt={props.data} />
          )}
    },
    {
      'columnName': 'end_date',
      'order': 9,
      'displayName': 'Estimated end date',
      'customComponent': (props) => {
        const date = moment(props.data, 'YYYY-MM-DD').format('DD/MM/YYYY');
        const val = date === 'Invalid date' ? '' : date;
        return (<span>{val}</span>);
      }
    }
  ];

  if (showService) {
    columnMetadata.push({
      'columnName': 'service_area',
      'order': 2,
      'displayName': 'Service area',
      'customCompareFn': (serv) => serv.name,
      'customComponent': (props) => (
        <span>{props.data.name}</span>
      )
    });
  };

  return (
    <Griddle
      results={projects}
      columns={columnMetadata.map(item => item['columnName'])}
      columnMetadata={columnMetadata}
      useGriddleStyles={false}
      bodyHeight={800}
      resultsPerPage={ projects.length }
      initialSort='name'
      showFilter={showFilter}
      filterPlaceholderText=''
      useCustomFilterComponent={true}
      customFilterComponent={FilterComponent}
    />
  );
}
