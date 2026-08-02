export class ISBN {
    private readonly value: string;

    constructor(value: string) {
        if (!this.validateISBN(value)) {
            throw new Error('Invalid ISBN');
        }
        this.value = value;
    }

    private validateISBN(isbn: string): boolean {
        // Implement ISBN validation logic here
        return true; // Placeholder for actual validation
    }

    public getValue(): string {
        return this.value;
    }
}

export class Email {
    private readonly value: string;

    constructor(value: string) {
        if (!this.validateEmail(value)) {
            throw new Error('Invalid Email');
        }
        this.value = value;
    }

    private validateEmail(email: string): boolean {
        // Implement email validation logic here
        return true; // Placeholder for actual validation
    }

    public getValue(): string {
        return this.value;
    }
}