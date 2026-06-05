# Codebase Architecture & File Mapping

This document provides a map of the repository's components, layout, and database structure to guide code generation and testing tasks.

## Application Structure

- **`main.py`**: The main FastAPI application entrypoint. Declares HTTP endpoints, configures CORS middleware, mounts static directories, and registers route endpoints.
- **`database.py`**: Setup for SQLAlchemy database engine, session local configurations, and DB dependency functions (`get_db`).
- **`models.py`**: SQLAlchemy database model definitions (e.g. `User`, `Garden`, `GardenPhoto`, `GardenUpdate`, `Plant`, `PlantUpdate`).
- **`schemas.py`**: Pydantic schemas/models for request validations and endpoint response serialization mapping.
- **`cron.py`**: Background cron job task scheduler running the AI processing pipeline of new gardens.
- **`nginx.conf` & `supervisord.conf`**: Process management and reverse proxy routing configurations inside the Cloud Run deployment environment.

## Services Layer (`services/`)
- **`services/auth.py`**: Authentication logic for validating tokens and external users.
- **`services/gcs.py`**: Google Cloud Storage helper routines to store and retrieve garden/plant photo assets.
- **`services/garden_processor.py`**: Core pipeline processor for new gardens, coordinating plant classification and health analysis.

## Test Suites (`tests/`)
- Contains pytest files verifying API behaviors.
- Integration tests must read the `BASE_URL` environment variable to run tests against the live target staging URL.
