/**
 * @quantumshield/api-client
 * Generated OpenAPI client placeholder
 */
export interface HealthResponse {
  status: string;
  version: string;
  environment: string;
  uptime_seconds: number;
  timestamp: string;
}

export const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
