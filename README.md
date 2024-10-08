# Backend for bike fitting API

DEV Setup:

- Start database and S3

```bash
docker-compose up -d
```

- Start lambda function

```bash
python serverless/processing.py --rp_debugger --rp_serve_api --rp_api_port 6969
```

- Start server

```bash
fastapi dev --reload
```

