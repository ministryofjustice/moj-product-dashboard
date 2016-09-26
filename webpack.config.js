var path = require('path');
var ExtractTextPlugin = require("extract-text-webpack-plugin");
var BundleTracker = require('webpack-bundle-tracker');

var directory = path.resolve(__dirname, "dashboard/assets");
var dist = path.resolve(directory, 'dist');

module.exports = {
  entry: [
    'babel-polyfill',
    path.resolve(directory, 'js/main.js'),
  ],
  output: {
    path: dist,
    publicPath: '/static/dist/',
    filename: "dashboard.[hash].js"
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
    new ExtractTextPlugin("dashboard.[hash].css"),
    new BundleTracker({
      path: dist,
      filename: 'webpack-stats.json'
    })
  ],
  devtool: 'source-map'
};
