const path = require('path');

module.exports = {
  mode: 'production',
  entry: './src/live2dcubismframework.ts',
  output: {
    path: path.resolve(__dirname, 'dist'),
    filename: 'live2dcubismframework.bundle.js',
    library: 'Live2DCubismFramework',
    libraryTarget: 'umd',
    globalObject: 'this'
  },
  module: {
    rules: [
      {
        test: /\.tsx?$/,
        use: [
          {
            loader: 'ts-loader',
            options: {
              transpileOnly: true  // Skip type checking - Live2DCubismCore is a runtime global
            }
          }
        ],
        exclude: /node_modules/
      }
    ]
  },
  resolve: {
    extensions: ['.ts', '.js'],
    alias: {
      '@': path.resolve(__dirname, 'src')
    }
  },
  externals: {}
};
