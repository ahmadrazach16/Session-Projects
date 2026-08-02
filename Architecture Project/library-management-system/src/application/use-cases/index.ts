import { LibraryService } from '../services';

export class AddBookUseCase {
  constructor(private readonly libraryService: LibraryService) {}

  async execute(bookData: { id?: string; title: string; author: string; isbn: string }) {
    return await this.libraryService.addBook(bookData);
  }
}

export class RemoveBookUseCase {
  constructor(private readonly libraryService: LibraryService) {}

  async execute(bookId: string) {
    return await this.libraryService.deleteBook(bookId);
  }
}

export class GetBooksUseCase {
  constructor(private readonly libraryService: LibraryService) {}

  async execute() {
    return await this.libraryService.getBooks();
  }
}