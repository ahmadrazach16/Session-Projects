# Library Management System

This project is a Library Management System built using TypeScript, following Clean Architecture principles. It provides core functionalities for managing books and users in a library setting.

## Features

- Add, update, and delete books
- Manage users
- Search for books by various criteria
- Integration with PostgreSQL or MySQL for data persistence
- RESTful API for interaction with the frontend

## Project Structure

```
library-management-system
├── src
│   ├── application
│   │   ├── services
│   │   └── use-cases
│   ├── domain
│   │   ├── entities
│   │   ├── repositories
│   │   └── value-objects
│   ├── infrastructure
│   │   ├── config
│   │   ├── database
│   │   └── persistence
│   ├── interfaces
│   │   ├── controllers
│   │   └── routes
│   ├── shared
│   │   └── utils
│   └── server.ts
├── tests
│   └── integration
├── .env.example
├── .gitignore
├── docker-compose.yml
├── package.json
├── tsconfig.json
└── README.md
```

## Setup Instructions

1. **Clone the repository:**
   ```
   git clone <repository-url>
   cd library-management-system
   ```

2. **Install dependencies:**
   ```
   npm install
   ```

3. **Configure environment variables:**
   Copy `.env.example` to `.env` and fill in the required values for your database connection.

4. **Run the application:**
   ```
   npm start
   ```

5. **Run tests:**
   ```
   npm test
   ```

## Usage

The API provides endpoints for managing library operations. You can use tools like Postman or curl to interact with the API.

## Contributing

Contributions are welcome! Please open an issue or submit a pull request for any enhancements or bug fixes.

## License

This project is licensed under the MIT License. See the LICENSE file for details.