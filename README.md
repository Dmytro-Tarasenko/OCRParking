# OCRParking Project

## Overview

OCRParking is an AI-powered parking management system that uses Optical Character Recognition (OCR) to automate vehicle
entry and exit based on license plate recognition. The project integrates various components, including machine learning
models, a FastAPI backend, and a user-friendly frontend to manage parking operations efficiently.

## Features

- Vehicle Entry and Exit Automation: Detects vehicles via uploaded images and manages parking operations such as entry,
  exit, and billing.
- User and Admin Management: Role-based access control for users and administrators.
- Billing and Payments: Users can view and pay for parking, and administrators can manage billing records.
- Parking Statistics: Admins can access detailed statistics about parking, users, and revenues.
- Blacklisting: Vehicles can be blacklisted based on user debts or other criteria.
- Machine Learning for OCR: Uses trained models for license plate recognition to identify vehicles.
- Dockerized Deployment: Fully containerized setup with Docker and Docker Compose.

## Project Structure

### Root Directory

- `Dockerfile`: Docker configuration for the project.
- `LICENSE`: License for the project.
- `Project_ocrparking_6.ipynb`: Jupyter notebook for documentation and experiments.
- `settings.py`: Project settings and configurations.

### Folders

- **admin/**: Admin-specific routes and functionality.
    - `routes.py`

- **auth/**: Authentication and authorization logic.
    - `auth.py`
    - `routes.py`

- **cameras/**: Vehicle detection and OCR-related utilities.
    - `routes.py`
    - `utils.py`

- **classify/**: Image classification models and scripts.
    - `predict.py`
    - `train.py`
    - `tutorial.ipynb`
    - `val.py`

- **data/**: Datasets and scripts for model training.
    - Various dataset configuration files (e.g., `ImageNet.yaml`, `coco128.yaml`, etc.)

- **db_models/**: Database models and initialization scripts.
    - `db.py`
    - `init_db.py`
    - `models.py`

- **frontend/**: Frontend templates and static assets.
    - `routes.py`
    - Static files: JS, CSS, and images.
    - HTML templates for user and admin pages.

- **migrations/**: Alembic database migrations.
    - Migration scripts and version control.

- **models/**: YOLO models and configurations for object detection.
    - Model configuration files for YOLO object detection.

- **ocr_ml/**: OCR machine learning logic for license plate recognition.
    - `plate_recognition.py`
    - Model files and other relevant scripts.

- **schemas/**: Pydantic schemas for API requests and responses.
    - `auth.py`
    - `cars.py`

- **segment/**: Image segmentation models and scripts.
    - `predict.py`
    - `train.py`

- **user/**: User-specific routes and functionality.
    - `routes.py`

- **utils/**: Utility scripts for various tasks.
    - Scripts for augmentations, loss calculation, and more.

## Technologies

The OCRParking project utilizes the following technologies:

- Python: The main programming language.
- FastAPI: Web framework for building APIs.
- PostgreSQL: Relational database for storing user, vehicle, and parking information.
- Docker: Containerization platform for deploying the application.
- Uvicorn: ASGI server for serving the FastAPI application.
- Alembic: Database migrations tool.
- SQLAlchemy: ORM for interacting with the PostgreSQL database.
- Pydantic: Data validation and parsing library.
- JWT: JSON Web Token for user authentication.
- HTMX: Frontend library for dynamic web interfaces.
- YOLOv5: Object detection model for license plate recognition (used in the OCR component).

## Libraries Used

Here is a list of the major libraries used in the project, as defined in pyproject.toml or requirements.txt:

- FastAPI: Web framework for Python to build APIs.
- SQLAlchemy: ORM for handling database interactions.
- Alembic: Tool for database migrations.
- Pydantic: For data validation and settings management.
- passlib: For secure password hashing.
- python-jose: Library for JWT creation and verification.
- asyncpg: PostgreSQL driver for asynchronous access.
- Uvicorn: ASGI server to run the FastAPI application.
- httpx: HTTP client for making asynchronous requests.
- htmx: For creating interactive and dynamic web pages.
- opencv-python: For handling image processing (used in OCR tasks).
- torch: PyTorch, used for machine learning tasks.
- numpy: Library for numerical operations (used in machine learning).
- scikit-learn: For model evaluation and preprocessing. 

These libraries are critical for both the backend API, user authentication, camera simulations, and machine learning
functionalities. Make sure to install them via the package manager of your choice.

## Setup and Installation

### Prerequisites

- Docker
- Docker Compose
- Python 3.11+
- Poetry (for managing dependencies)
- Installation Steps

1. Clone the repository:
   git clone https://github.com/Dmytro-Tarasenko/OCRParking.git
   cd OCRParking

2. Install dependencies:
   If using Poetry:
   poetry install

If you are using pip:
pip install -r requirements.txt

3. Create a .env file by copying from the example dev.env:
   cp dev.env .env
   Fill in the required environment variables in the .env file.

4. Set Up the Database:

- Start Docker to create the containers:
  docker-compose up -d
- Create a PostgreSQL database with the name specified in your .env file, for example, ocr_parking.
- Apply database migrations:
  alembic upgrade head


5. Run the application:
   Start the application locally using Uvicorn::
   uvicorn main:app --reload


6. Access the application at http://localhost:8000 or 127.0.0.1:8000 in your web browser.

## Usage

- Admin Interface: Access the admin dashboard for managing users, vehicles, and tariffs.
- User Interface: Users can register, log in, view parking history, add cars, and make payments.
- Cameras Simulation: Simulate vehicle entry/exit by uploading images of license plates.

## Machine Learning Components

- YOLO Models: Utilized for object detection and vehicle recognition.
- OCR for License Plates: Machine learning model trained for recognizing license plates from images.
- Classification and Segmentation: Models for fine-tuning image processing tasks.

## Contributing

1. Fork the repository
2. Create your feature branch (git checkout -b feature/your-feature)
3. Commit your changes (git commit -m 'Add some feature')
4. Push to the branch (git push origin feature/your-feature)
5. Create a new Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## 👤 Made by

Made with  by "Project Team № 4":\
🔥 [Dmytro Tarasenko](https://github.com/Dmytro-Tarasenko)\
🔥 [Maksym Melnyk](https://github.com/Resst94)\
🔥 [Anzhelika Kodlubovska](https://github.com/AnzhelikaKodlubovska)\
🔥 [Sergiy Chabanchuk](https://github.com/chabanchuk)\
🔥 [Oleksandr Zabolotnii](https://github.com/0leksandrZahar0vi4)


&#xa0;

<a href="#top">Back to top</a>