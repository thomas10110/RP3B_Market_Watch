The application should be structured into the following modules:

- `app.py`: Main Flask application, handling web routes and orchestrating the other modules.
- `database.py`: Manages the SQLite database, including schema creation and all CRUD operations.
- `fetcher.py`: Responsible for fetching price data from Finnhub and Marketstack APIs.
- `notifier.py`: Handles sending email notifications via SMTP.
- `config.py`: Stores all configuration variables, such as API keys and email settings.

Follow these instructions when developing the application:

1.  **Use SQLite for the database.** The schema should be created and managed in `database.py`.
2.  **Implement a modern UI.** The frontend should be clean, responsive, and user-friendly.
3.  **Use Flask for the web server.** The main application logic should reside in `app.py`.
4.  **Implement a background worker.** A separate thread or process should be used to fetch prices and send notifications every 10 seconds.
5.  **Add robust error handling.** The application should be able to handle unexpected errors and send a notification to the admin email.
6.  **Keep the code simple and readable.** The code should be well-commented and easy to understand.
7.  **Ensure compatibility with Raspberry Pi 3B.** All dependencies and code should be compatible with the Raspberry Pi environment.