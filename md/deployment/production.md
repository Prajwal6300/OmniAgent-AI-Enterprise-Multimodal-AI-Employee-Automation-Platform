# Deployment — Production Hardening & Reverse Proxy Setup

## Status
**Status:** ✅ IMPLEMENTED (Uvicorn / Gunicorn Workers & Nginx TLS Setup)

---

## 1. Uvicorn Worker Sizing & Process Management

For production deployments, the backend is run via **Gunicorn managing Uvicorn async workers**:
```bash
gunicorn app.main:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000 \
  --timeout 120 \
  --keep-alive 5 \
  --access-logfile /app/logs/access.log \
  --error-logfile /app/logs/error.log
```

Formula for optimal worker processes:
$$\text{Workers} = (2 \times \text{CPU Cores}) + 1$$

---

## 2. Nginx Reverse Proxy Configuration

```nginx
server {
    listen 443 ssl http2;
    server_name portal.omniagent.enterprise.io;

    ssl_certificate /etc/letsencrypt/live/omniagent/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/omniagent/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;

    # Frontend Next.js Application
    location / {
        proxy_pass http://frontend:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # Backend FastAPI REST & SSE Streaming Endpoints
    location /api/ {
        proxy_pass http://backend:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;

        # Disable buffering for SSE real-time token streaming
        proxy_buffering off;
        proxy_cache off;
        proxy_read_timeout 600s;
    }
}
```
