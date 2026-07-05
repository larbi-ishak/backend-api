from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import redis
import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("backend-api")

app = FastAPI(title="Infra Telemetry API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_methods=["GET"],
    allow_headers=["*"],
)

REDIS_HOST = os.getenv('REDIS_HOST', 'redis')
REDIS_PORT = int(os.getenv('REDIS_PORT', 6379))

pool = redis.ConnectionPool(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)
r = redis.Redis(connection_pool=pool)

@app.get("/healthz")
def health_check():
    try:
        r.ping()
        return {"status": "ok", "redis": "connected"}
    except redis.ConnectionError:
        raise HTTPException(status_code=503, detail="Redis connection failed")

@app.get("/api/v1/nodes")
def get_node_status():
    try:
        raw_data = r.hgetall('global_infra_status')
        parsed_data = {}
        for component, payload in raw_data.items():
            state, timestamp = payload.split('|')
            parsed_data[component] = {"state": state, "last_seen": timestamp}
        
        return {"components": parsed_data}
    except Exception as e:
        logger.error(f"Failed to fetch telemetry: {e}")
        raise HTTPException(status_code=500, detail="Internal server error fetching telemetry")
