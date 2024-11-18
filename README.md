# Bike Fitting API Backend

![GitHub License](https://img.shields.io/badge/license-AGPLv3-blue)
![GitHub Actions Workflow Status](https://img.shields.io/github/actions/workflow/status/camber-bikes/bike-fitting-api/build-backend.yml?label=backend%20build)
![GitHub Actions Workflow Status](https://img.shields.io/github/actions/workflow/status/camber-bikes/bike-fitting-api/migrate-db.yml?label=database%20migrations)
![GitHub Actions Workflow Status](https://img.shields.io/github/actions/workflow/status/camber-bikes/bike-fitting-api/build-serverless.yml?label=serverless%20build)
![GitHub commit activity](https://img.shields.io/github/commit-activity/m/camber-bikes/bike-fitting-app)
![Static Badge](https://img.shields.io/badge/%F0%9F%8D%BA_Buy_us_a_beer-yellow)

Backend service for the Camber Bikes Bike Fitting Application, providing RESTful API endpoints and RunPod serverless functions for bike fitting calculations and data processing.

Built for the "Silicon Valley IT Talent Program 2024" by Team "Camber Bikes".

## Prerequisites

Before you begin, ensure you have installed:
- Python 3.11 or higher
- Docker & Docker Compose

## Development Setup

### 1. Start Required Services

Launch the database and S3 storage using Docker:
```bash
docker-compose up -d
```

This will start:
- PostgreSQL database on port 5432
- MinIO S3-compatible storage on port 9000
- MinIO Console on port 9001

### 2. Start Serverless Functions

Navigate to the serverless directory and start the RunPod serverless function in debug mode:
``` bash
cd serverless
python -m venv .venv # Create venv
source .venv/bin/activate # Activate venv
pip install -r requirements.txt # Install Requirements
python main.py --rp_debugger --rp_serve_api --rp_api_port 6969 # Launch Serverless
```

Serverless endpoints will be available at:
- HTTP: http://localhost:6969

### 3. Launch FastAPI Server

Start the FastAPI development server with hot reload:
```bash
python -m venv .venv # Create venv
source .venv/bin/activate # Activate venv
pip install -r requirements.txt # Install Requirements
fastapi dev --reload # Launch Fastapi
```

The API will be available at http://localhost:8000

## Key Technologies

- **FastAPI**: Modern web framework for building APIs
- **SQLAlchemy**: SQL toolkit and ORM
- **httpx**: http requests
- **Pydantic**: Data validation using Python type annotations
- **RunPod**: Serverless GPU compute for bike fitting calculations
- **PostgreSQL**: Primary database
- **MinIO**: S3-compatible object storage for DEV
- **Docker**: Containerization and local development

## API Documentation

Once the server is running, access the interactive API documentation at:
- Swagger UI: http://localhost:8000/docs
## Environment Variables

Create a `.env` file in the root directory by copying the `.env.example` file

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes using [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/) (`git commit -m 'feat(scope): what did you change'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the AGPLv3 License - see the [LICENSE](LICENSE) file for details.

---
Built with ❤️ by Camber Bikes

## Support Us

<a href="https://www.buymeacoffee.com/camberbikes"><img src="https://img.buymeacoffee.com/button-api/?text=Buy us a Beer &emoji=🍺&slug=camberbikes&button_colour=FFDD00&font_colour=000000&font_family=Arial&outline_colour=000000&coffee_colour=ffffff" /></a>