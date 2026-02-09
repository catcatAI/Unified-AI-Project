const path = require('path');

module.exports = {
  mode: 'production',
  entry: './dist/live2dcubismframework.js',
  output: {
    path: path.resolve(__dirname, 'dist'),
    filename: 'live2dcubismframework.bundle.js',
    library: 'Live2DCubismFramework',
    libraryTarget: 'umd',
    globalObject: 'this'
  },
  resolve: {
    extensions: ['.js', '.ts'],
    alias: {
      '@': path.resolve(__dirname, 'src')
    }
  },
  externals: {
  }
};
