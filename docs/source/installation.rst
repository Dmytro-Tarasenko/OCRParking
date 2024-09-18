Installation
============

To install OCRParking, follow these steps:

1. Clone the repository:

   .. code-block:: bash

      git clone https://github.com/Dmytro-Tarasenko/OCRParking.git

2. Navigate to the project directory:

   .. code-block:: bash

      cd OCRParking

3. Install dependencies:

   If you are using **Poetry**, run the following command:

   .. code-block:: bash

      poetry install

   If you are using **pip**, install dependencies from the `requirements.txt` file:

   .. code-block:: bash

      pip install -r requirements.txt

4. Set up environment variables:

   Copy the `dev.env` file to `.env` and fill in the required environment variables, such as `JWT_SECRET_KEY`, database connection details, etc.

   .. code-block:: bash

      cp dev.env .env

5. Set up the database:

   a. Start Docker to create the necessary containers:

   .. code-block:: bash

      docker-compose up -d

   b. Create a PostgreSQL database with the name specified in your `.env` file (for example, `ocr_parking`).

   c. Apply database migrations:

   .. code-block:: bash

      alembic upgrade head

6. Run the project:

   Start the application locally using **Uvicorn**:

   .. code-block:: bash

      uvicorn main:app --reload

7. Access the application:

   Open your web browser and go to the following URL:

   .. code-block:: bash

      http://localhost:8000
