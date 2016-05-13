#!/bin/bash

echo "****** CREATING DASHBOARD DATABASE ******"
gosu postgres psql <<- EOSQL
   CREATE DATABASE dashboard ENCODING 'UTF8';
EOSQL
echo ""
echo "****** DASHBOARD DATABASE CREATED ******"
