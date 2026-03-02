from fastapi import FastAPI
from .routes.inbound_routes import router as inbound_router

app = FastAPI(title="Customer Success Digital FTE - Phase 1 Prototype")

# Include the inbound routes
app.include_router(inbound_router)

@app.get("/")
def read_root():
    return {"message": "Welcome to the Customer Success Digital FTE Prototype"}

@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "Customer Success Digital FTE"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)