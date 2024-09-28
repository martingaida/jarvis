import webpack from 'webpack';
import { CustomWebpackBrowserSchema, TargetOptions } from '@angular-builders/custom-webpack';
import * as dotenv from 'dotenv';

export default (
  config: webpack.Configuration,
  options: CustomWebpackBrowserSchema,
  targetOptions: TargetOptions
) => {
  const env = dotenv.config().parsed;
  const envKeys = Object.keys(env || {}).reduce<Record<string, string>>((prev, next) => {
    prev[`process.env.${next}`] = JSON.stringify(env?.[next]);
    return prev;
  }, {});

  config.plugins = config.plugins || [];
  config.plugins.push(new webpack.DefinePlugin({
    ...envKeys,
    'process.env': '{}'
  }));
  return config;
};