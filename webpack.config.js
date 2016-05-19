var directory = __dirname + "/dashboard/apps/prototype/static/prototype/js/";
module.exports = {
  entry: [
  'babel-polyfill',
  directory + 'main.js'
  ],
  output: {
    path: directory,
    filename: "bundle.js"
  },

  module: {
    loaders: [
      {
        test: /.js$/,
        loader: 'babel-loader',
        exclude: /node_modules/,
        query: {
          presets: ['es2015']
        }
      }
    ]
  }
};
