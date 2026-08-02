import { Router } from 'express';
import { LibraryController } from '../controllers';

const router = Router();
const controller = new LibraryController();

router.post('/books', controller.addBook.bind(controller));
router.delete('/books/:id', controller.removeBook.bind(controller));
router.get('/books', controller.getBooks.bind(controller));
router.post('/users', controller.addUser.bind(controller));
router.delete('/users/:id', controller.removeUser.bind(controller));
router.get('/users', controller.getUsers.bind(controller));

export default router;