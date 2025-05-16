const path = require('path');
const HtmlWebpackPlugin = require('html-webpack-plugin');
const { CleanWebpackPlugin } = require('clean-webpack-plugin');
const CopyWebpackPlugin = require('copy-webpack-plugin');
const webpack = require('webpack');

module.exports = (env, argv) => {
  const mode = argv.mode || process.env.NODE_ENV || 'development';
  console.log(`Building in ${mode} mode`);
  
  return {
    mode,
    entry: {
      main: './src/index.tsx'
    },
    output: {
      path: path.resolve(__dirname, 'dist'),
      filename: '[name].[contenthash].js',
      publicPath: '/'
    },
    devtool: mode === 'development' ? 'inline-source-map' : 'source-map',
    devServer: {
      static: './dist',
      hot: true,
      historyApiFallback: true,
      host: '0.0.0.0',
      port: process.env.PORT || 3000
    },
    module: {
      rules: [
        {
          test: /\.tsx?$/,
          use: 'ts-loader',
          exclude: /node_modules/
        },
        {
          test: /\.css$/,
          use: ['style-loader', 'css-loader']
        },
        {
          test: /\.(png|svg|jpg|jpeg|gif|mp3|wav)$/i,
          type: 'asset/resource'
        }
      ]
    },
    resolve: {
      extensions: ['.tsx', '.ts', '.js'],
      fallback: {
        process: require.resolve('process/browser'),
        "path": require.resolve("path-browserify")
      }
    },
    plugins: [
      new CleanWebpackPlugin(),
      new HtmlWebpackPlugin({
        template: './public/index.html',
        filename: 'index.html',
        inject: 'body'
      }),
      new webpack.DefinePlugin({
        'process.env.NODE_ENV': JSON.stringify(mode),
        'process.env.REACT_APP_SOCKET_URL': JSON.stringify(process.env.REACT_APP_SOCKET_URL || 'http://localhost'),
        'process.env.REACT_APP_SOCKET_PATH': JSON.stringify(process.env.REACT_APP_SOCKET_PATH || '/socket.io'),
        'process.env.REACT_APP_LOGS_ENDPOINT': JSON.stringify(process.env.REACT_APP_LOGS_ENDPOINT || '/logs'),
        'process.env.REACT_APP_SERVICE_NAME': JSON.stringify(process.env.REACT_APP_SERVICE_NAME || 'web-frontend'),
        'process.env.REACT_APP_LOGS_BATCH_SIZE': JSON.stringify(process.env.REACT_APP_LOGS_BATCH_SIZE || '10')
      })
    ],
    optimization: {
      splitChunks: {
        chunks: 'all'
      }
    },
    performance: {
      hints: false, // отключить эти предупреждения
    },
  };
}; 