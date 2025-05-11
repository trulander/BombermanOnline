const path = require('path');
const HtmlWebpackPlugin = require('html-webpack-plugin');
const { CleanWebpackPlugin } = require('clean-webpack-plugin');
const CopyWebpackPlugin = require('copy-webpack-plugin');
const webpack = require('webpack');

module.exports = (env, argv) => {
  const isProduction = process.env.NODE_ENV === 'production';

  return {
    entry: './src/index.ts',
    module: {
      rules: [
        {
          test: /\.tsx?$/,
          use: 'ts-loader',
          exclude: /node_modules/,
        },
        {
          test: /\.(png|svg|jpg|jpeg|gif|mp3|wav)$/i,
          type: 'asset/resource',
        },
      ],
    },
    resolve: {
      extensions: ['.tsx', '.ts', '.js'],
      fallback: {
        process: require.resolve('process/browser'),
        "path": require.resolve("path-browserify")
      }
    },
    output: {
      filename: 'bundle.[contenthash].js',
      path: path.resolve(__dirname, 'dist'),
    },
    plugins: [
      new CleanWebpackPlugin(),
      new HtmlWebpackPlugin({
        template: 'src/index.html',
      }),
      new CopyWebpackPlugin({
        patterns: [
          { from: 'src/assets', to: 'assets', noErrorOnMissing: true }
        ],
      }),
      new webpack.DefinePlugin({
        'process.env.NODE_ENV': JSON.stringify(process.env.NODE_ENV || 'development'),
        'process.env.LOGS_ENDPOINT': JSON.stringify(process.env.LOGS_ENDPOINT || '/logs'),
        'process.env.SERVICE_NAME': JSON.stringify(process.env.SERVICE_NAME || 'web-frontend'),
        'process.env.SOCKET_URL': JSON.stringify(process.env.SOCKET_URL || 'http://localhost'),
        'process.env.SOCKET_PATH': JSON.stringify(process.env.SOCKET_PATH || '/socket.io'),
      }),
      new webpack.ProvidePlugin({
        process: 'process/browser',
      }),
      new webpack.BannerPlugin({
        banner: `
          window.NODE_ENV = "${process.env.NODE_ENV || 'development'}";
          window.LOGS_ENDPOINT = "${process.env.LOGS_ENDPOINT || '/logs'}";
          window.SERVICE_NAME = "${process.env.SERVICE_NAME || 'web-frontend'}";
          window.SOCKET_URL = "${process.env.SOCKET_URL || 'http://localhost'}";
          window.SOCKET_PATH = "${process.env.SOCKET_PATH || '/socket.io'}";
        `,
        raw: true,
        entryOnly: true
      }),
    ],
    devServer: {
      static: {
        directory: path.join(__dirname, 'dist'),
      },
      compress: true,
      port: 3000,
      proxy: {
        '/logs': {
          target: process.env.LOGS_ENDPOINT || 'http://localhost',
          secure: false,
          changeOrigin: true,
        },
        [process.env.SOCKET_PATH || '/socket.io']: { // Динамический ключ на основе SOCKET_PATH
          target: process.env.SOCKET_URL || 'http://localhost',
          secure: false,
          changeOrigin: true,
          ws: true,
        },
      }
    },
  };
};
