export const logger = (message: string): void => {
    console.log(`[LOG] ${new Date().toISOString()}: ${message}`);
};

export const errorHandler = (error: Error): void => {
    console.error(`[ERROR] ${new Date().toISOString()}: ${error.message}`);
};