import { Book, User } from '../../domain/entities';
import { LibraryRepository } from '../../domain/repositories';

export class LibraryService {
  private readonly libraryRepository: LibraryRepository;

  constructor(libraryRepository: LibraryRepository) {
    this.libraryRepository = libraryRepository;
  }

  async addBook(bookData: { id?: string; title: string; author: string; isbn: string }): Promise<void> {
    const book = new Book(
      bookData.id ?? `${Date.now()}`,
      bookData.title,
      bookData.author,
      new Date(),
      bookData.isbn,
    );

    await this.libraryRepository.addBook(book);
  }

  async updateBook(bookId: string, bookData: Partial<Book>): Promise<void> {
    const book = await this.libraryRepository.findBookById(bookId);
    if (book) {
      book.update(bookData);
      await this.libraryRepository.updateBook(book);
    }
  }

  async deleteBook(bookId: string): Promise<void> {
    await this.libraryRepository.removeBook(bookId);
  }

  async getBooks(): Promise<Book[]> {
    return await this.libraryRepository.getAllBooks();
  }

  async addUser(userData: { id?: string; name: string; email: string }): Promise<void> {
    const user = new User(
      userData.id ?? `${Date.now()}`,
      userData.name,
      userData.email,
      new Date(),
    );

    await this.libraryRepository.addUser(user);
  }

  async updateUser(userId: string, userData: Partial<User>): Promise<void> {
    const user = await this.libraryRepository.findUserById(userId);
    if (user) {
      user.update(userData);
      await this.libraryRepository.updateUser(user);
    }
  }

  async deleteUser(userId: string): Promise<void> {
    await this.libraryRepository.removeUser(userId);
  }

  async getUsers(): Promise<User[]> {
    return await this.libraryRepository.getAllUsers();
  }
}