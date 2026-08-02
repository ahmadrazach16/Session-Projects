import request from 'supertest';
import { app } from '../../src/server'; // Adjust the path as necessary
import { LibraryService } from '../../src/application/services/index';
import { LibraryRepository } from '../../src/domain/repositories/index';

describe('Library Management System Integration Tests', () => {
    let libraryService: LibraryService;
    let libraryRepository: LibraryRepository;

    beforeAll(() => {
        // Initialize the library service and repository
        libraryRepository = new LibraryRepository(); // Mock or actual implementation
        libraryService = new LibraryService(libraryRepository);
    });

    afterAll(async () => {
        // Clean up resources, if necessary
    });

    it('should add a new book', async () => {
        const newBook = {
            title: 'Test Book',
            author: 'Test Author',
            isbn: '1234567890',
        };

        const response = await request(app)
            .post('/api/books')
            .send(newBook)
            .expect(201);

        expect(response.body).toHaveProperty('id');
        expect(response.body.title).toBe(newBook.title);
    });

    it('should retrieve all books', async () => {
        const response = await request(app)
            .get('/api/books')
            .expect(200);

        expect(Array.isArray(response.body)).toBe(true);
    });

    it('should remove a book', async () => {
        const bookId = 1; // Replace with a valid book ID

        const response = await request(app)
            .delete(`/api/books/${bookId}`)
            .expect(204);

        expect(response.body).toEqual({});
    });
});