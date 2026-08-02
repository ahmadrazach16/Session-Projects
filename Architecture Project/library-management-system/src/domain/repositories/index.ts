import { Book, User } from '../entities';

export interface LibraryRepository {
  findBookById(id: string): Promise<Book | null>;
  addBook(book: Book): Promise<void>;
  updateBook(book: Book): Promise<void>;
  removeBook(id: string): Promise<void>;
  getAllBooks(): Promise<Book[]>;

  findUserById(id: string): Promise<User | null>;
  addUser(user: User): Promise<void>;
  updateUser(user: User): Promise<void>;
  removeUser(id: string): Promise<void>;
  getAllUsers(): Promise<User[]>;
}