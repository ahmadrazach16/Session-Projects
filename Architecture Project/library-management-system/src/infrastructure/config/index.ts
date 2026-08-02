import { config as dotenvConfig } from 'dotenv';

dotenvConfig();

const databaseConfig = {
  host: process.env.DB_HOST || 'localhost',
  port: parseInt(process.env.DB_PORT || '5432', 10),
  username: process.env.DB_USER || 'user',
  password: process.env.DB_PASS || 'password',
  database: process.env.DB_NAME || 'library_management',
  dialect: process.env.DB_DIALECT || 'postgres',
};

const appConfig = {
  port: parseInt(process.env.APP_PORT || process.env.PORT || '3000', 10),
  env: process.env.NODE_ENV || 'development',
};

const config = {
  database: databaseConfig,
  app: appConfig,
};

export { config, databaseConfig, appConfig };