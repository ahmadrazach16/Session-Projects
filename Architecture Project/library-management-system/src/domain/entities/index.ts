export class Book {
  constructor(
    public id: string,
    public title: string,
    public author: string,
    public publishedDate: Date,
    public isbn: string,
  ) {}

  update(data: Partial<Book>): void {
    if (data.title !== undefined) this.title = data.title;
    if (data.author !== undefined) this.author = data.author;
    if (data.publishedDate !== undefined) this.publishedDate = data.publishedDate;
    if (data.isbn !== undefined) this.isbn = data.isbn;
  }
}

export class User {
  constructor(
    public id: string,
    public name: string,
    public email: string,
    public membershipDate: Date,
  ) {}

  update(data: Partial<User>): void {
    if (data.name !== undefined) this.name = data.name;
    if (data.email !== undefined) this.email = data.email;
    if (data.membershipDate !== undefined) this.membershipDate = data.membershipDate;
  }
}