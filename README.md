# emmc-migration-service
Backend service to remotely enable SD-to-eMMC migration

# start
python3 -m venv .venv
source .venv/bin/activate
uvicorn main:app --reload

## API Documentation
FastAPI generates interactive documentation automatically. Once the server is running, open:
http://localhost:8000/docs

# Testing

Install develop dependencies:
```bash
pip install -r requirements-dev.txt
```

Launch tests:
```bash
pytest -v
```
