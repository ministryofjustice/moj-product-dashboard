var path = require('path');

var directory = path.resolve(__dirname, "dashboard/apps/prototype/static");
var ExtractTextPlugin = require("extract-text-webpack-plugin");

module.exports = {
  entry: [
    'babel-polyfill',
    path.resolve(directory, 'js/main.js'),
  ],
  output: {
    path: path.resolve(directory, 'dist'),
    filename: "prototype.js"
  },

  module: {
    loaders: [
      {
        test: /.js$/,
        loader: 'babel-loader',
        exclude: /node_modules/,
        query: {
          presets: ['es2015', 'react']
        }
      },
      {
        test: /\.css$/,
        loader: ExtractTextPlugin.extract("style-loader", "css-loader")
      }
    ],
    resolve: {
      alias: {
        'jquery': 'jquery/src/jquery',
        'select2': 'select2/src/js/jquery.select2'
      }
    }
  },
  plugins: [
    new ExtractTextPlugin("prototype.css")
  ],
  devtool: 'source-map'
};
