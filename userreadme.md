# DocVerify AI — User Guide
## How to Run

### Clone and Start Services
```bash
git clone [https://github.com/Bhaskary07/DocVerify-AI.git](https://github.com/Bhaskary07/DocVerify-AI.git)
cd DocVerify-AI

### To run
docker compose up --build -d

### Check running containers with:
 docker compose ps
 
### Access URLs
Frontend Web UI: http://localhost:3000 (mapped from container port 80)
Backend Health Check: http://localhost:8000/health 
Backend API Documentation (Swagger UI): http://localhost:8000/docs 

### To stop
 docker compose down


