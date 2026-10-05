// Mirrors the backend HealthResponse Pydantic model (app/api/routes/health.py).
export interface HealthResponse {
  status: string;
  app: string;
  environment: string;
  database: "connected" | "disconnected";
}
