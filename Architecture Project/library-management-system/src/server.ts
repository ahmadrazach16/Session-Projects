import express, { Application, Request, Response } from 'express';
import { LibraryController } from './interfaces/controllers';
import { config } from './infrastructure/config';

const app: Application = express();
const PORT = config.app.port;

app.use(express.json());

const libraryController = new LibraryController();
app.use('/api/library', libraryController.router);

app.get('/', (_req: Request, res: Response) => {
  res.status(200).json({
    success: true,
    message: 'Library API is running.',
  });
});

app.listen(PORT, () => {
  console.log(`🚀 Server is running on http://localhost:${PORT}`);
});
