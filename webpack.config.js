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
    publicPath: '/static/dist/',
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
      },
      {
        test: /\.jpe?g$|\.gif$|\.png$|\.svg$|\.woff$|\.ttf$/,
        loader: "file-loader"
      }
    ]
  },
  plugins: [
    new ExtractTextPlugin("prototype.css")
  ],
  devtool: 'source-map'
};
