# OCRParking Project

## Overview

OCRParking is an AI-powered parking management system that uses Optical Character Recognition (OCR) to automate vehicle entry and exit based on license plate recognition. The project integrates various components, including machine learning models, a FastAPI backend, and a user-friendly frontend to manage parking operations efficiently.

## Features

- Vehicle Entry and Exit Automation: Detects vehicles via uploaded images and manages parking operations such as entry, exit, and billing.
- User and Admin Management: Role-based access control for users and administrators.
- Billing and Payments: Users can view and pay for parking, and administrators can manage billing records.
- Parking Statistics: Admins can access detailed statistics about parking, users, and revenues.
- Blacklisting: Vehicles can be blacklisted based on user debts or other criteria.
- Machine Learning for OCR: Uses trained models for license plate recognition to identify vehicles.
- Dockerized Deployment: Fully containerized setup with Docker and Docker Compose.

## Project Structure

├── Dockerfile                       # Docker configuration for the project
├── LICENSE                          # License for the project
├── Project_ocrparking_6.ipynb        # Jupyter notebook for documentation and experiments
├── admin/                           # Admin-specific routes and functionality
├── auth/                            # Authentication and authorization logic
├── cameras/                         # Vehicle detection and OCR-related utilities
├── classify/                        # Image classification models and scripts
├── data/                            # Datasets and scripts for model training
├── db_models/                       # Database models and initialization scripts
├── frontend/                        # Frontend templates and static assets
├── migrations/                      # Alembic database migrations
├── models/                          # YOLO models and configurations for object detection
├── ocr_ml/                          # OCR machine learning logic for license plate recognition
├── schemas/                         # Pydantic schemas for API requests and responses
├── segment/                         # Image segmentation models and scripts
├── settings.py                      # Project settings and configurations
├── user/                            # User-specific routes and functionality
├── utils/                           # Utility scripts for various tasks

## Setup and Installation

### Prerequisites
- Docker
- Docker Compose
- Python 3.8+
- Poetry (for managing dependencies)
- Installation Steps

1. Clone the repository:
git clone https://github.com/your-repo/ocr-parking.git
cd ocr-parking

2. Install dependencies: If using Poetry:
poetry install

3. Set up environment variables: Copy .env.example to .env and modify the environment variables accordingly:
cp dev.env .env

4. Initialize the database: Run the following commands to apply migrations:
alembic upgrade head

5. Run the application:
With Docker:
docker-compose up --build

- Without Docker (local environment):
uvicorn main:app --reload

6. Access the application: Open your browser and navigate to:
http://localhost:8000

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