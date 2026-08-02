import { Request, Response, Router } from 'express';

export class LibraryController {
    public router: Router;
    private books: Array<{ id: string; title: string; author: string; isbn: string }>;
    private users: Array<{ id: string; name: string; email: string }>;

    constructor() {
        this.router = Router();
        this.books = [];
        this.users = [];

        this.router.post('/books', this.addBook.bind(this));
        this.router.delete('/books/:id', this.removeBook.bind(this));
        this.router.get('/books', this.getBooks.bind(this));
        this.router.post('/users', this.addUser.bind(this));
        this.router.delete('/users/:id', this.removeUser.bind(this));
        this.router.get('/users', this.getUsers.bind(this));
    }

    public async addBook(req: Request, res: Response): Promise<Response> {
        const { title, author, isbn } = req.body;
        const book = { id: `${Date.now()}`, title, author, isbn };
        this.books.push(book);
        return res.status(201).json({ message: 'Book added', book });
    }

    public async removeBook(req: Request, res: Response): Promise<Response> {
        const { id } = req.params;
        this.books = this.books.filter((book) => book.id !== id);
        return res.status(204).send();
    }

    public async getBooks(_req: Request, res: Response): Promise<Response> {
        return res.status(200).json(this.books);
    }

    public async addUser(req: Request, res: Response): Promise<Response> {
        const { name, email } = req.body;
        const user = { id: `${Date.now()}`, name, email };
        this.users.push(user);
        return res.status(201).json({ message: 'User added', user });
    }

    public async removeUser(req: Request, res: Response): Promise<Response> {
        const { id } = req.params;
        this.users = this.users.filter((user) => user.id !== id);
        return res.status(204).send();
    }

    public async getUsers(_req: Request, res: Response): Promise<Response> {
        return res.status(200).json(this.users);
    }
}