import { Book, User } from '../../domain/entities';
import { LibraryRepository } from '../../domain/repositories';

export class LibraryRepositoryImpl implements LibraryRepository {
  private readonly books: Book[] = [];
  private readonly users: User[] = [];

  async findBookById(id: string): Promise<Book | null> {
    return this.books.find((book) => book.id === id) ?? null;
  }

  async addBook(book: Book): Promise<void> {
    this.books.push(book);
  }

  async updateBook(book: Book): Promise<void> {
    const index = this.books.findIndex((item) => item.id === book.id);
    if (index >= 0) {
      this.books[index] = book;
    }
  }

  async removeBook(id: string): Promise<void> {
    const index = this.books.findIndex((book) => book.id === id);
    if (index >= 0) {
      this.books.splice(index, 1);
    }
  }

  async getAllBooks(): Promise<Book[]> {
    return [...this.books];
  }

  async findUserById(id: string): Promise<User | null> {
    return this.users.find((user) => user.id === id) ?? null;
  }

  async addUser(user: User): Promise<void> {
    this.users.push(user);
  }

  async updateUser(user: User): Promise<void> {
    const index = this.users.findIndex((item) => item.id === user.id);
    if (index >= 0) {
      this.users[index] = user;
    }
  }

  async removeUser(id: string): Promise<void> {
    const index = this.users.findIndex((user) => user.id === id);
    if (index >= 0) {
      this.users.splice(index, 1);
    }
  }

  async getAllUsers(): Promise<User[]> {
    return [...this.users];
  }
}