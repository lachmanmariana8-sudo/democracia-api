"""
Democrac.IA Backend API - Railway Edition
FastAPI server with mock data for production demo
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import os
from typing import List, Dict, Any
from datetime import datetime

# Configuration
app = FastAPI(
    title="Democrac.IA API",
    version="2.0.0",
    description="Electoral Observation Platform API"
)

# CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mock data for demo
MOCK_ELECTIONS = [
    {"id": 1, "country_iso2": "UG", "country_name": "Uganda", "election_type": "Presidential", "election_date": "2026-02-15", "status": "ACTIVE"},
    {"id": 2, "country_iso2": "NG", "country_name": "Nigeria", "election_type": "General", "election_date": "2026-03-01", "status": "ACTIVE"},
    {"id": 3, "country_iso2": "CO", "country_name": "Colombia", "election_type": "Congressional", "election_date": "2026-03-15", "status": "ACTIVE"},
    {"id": 4, "country_iso2": "CR", "country_name": "Costa Rica", "election_type": "Presidential", "election_date": "2026-04-06", "status": "ACTIVE"},
    {"id": 5, "country_iso2": "EC", "country_name": "Ecuador", "election_type": "Referendum", "election_date": "2026-05-01", "status": "PENDING"},
]

MOCK_OBSERVATIONS = [
    {"id": 1, "category": "IRREGULARIDAD", "title": "Posibles irregularidades en padrón electoral", "severity": "ALERTA", "captured_at": "2026-02-06 10:30:00", "source_name": "Electoral Commission", "country_iso2": "UG"},
    {"id": 2, "category": "TRANSPARENCIA", "title": "Demoras en publicación de resultados", "severity": "CRITICO", "captured_at": "2026-02-06 11:15:00", "source_name": "INEC Nigeria", "country_iso2": "NG"},
    {"id": 3, "category": "VOTO_EXTERIOR", "title": "Centros de votación sin supervisión", "severity": "MODERADO", "captured_at": "2026-02-06 12:00:00", "source_name": "OAS Mission", "country_iso2": "CO"},
]

@app.get("/")
def read_root():
    """Health check endpoint"""
    return {
        "status": "online",
        "system": "Democrac.IA API v2.0.0",
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/api/dashboard/stats")
def get_dashboard_stats():
    """Main dashboard KPIs"""
    return {
        "total_observations": 1247,
        "critical_risk": 23,
        "overseas_monitor": 45,
        "ire_index": 67.5,
        "active_elections": len([e for e in MOCK_ELECTIONS if e["status"] == "ACTIVE"])
    }

@app.get("/api/elections")
def get_elections():
    """List of active elections"""
    results = []
    for e in MOCK_ELECTIONS:
        if e["status"] == "ACTIVE":
            results.append({
                "id": e["id"],
                "country_iso2": e["country_iso2"],
                "election_date": e["election_date"],
                "election_type": e["election_type"],
                "status": e["status"],
                "countries": {
                    "name": e["country_name"],
                    "iso2": e["country_iso2"]
                }
            })
    return results

@app.get("/api/elections/{iso}")
def get_election_detail(iso: str):
    """Election details by country ISO code"""
    election = next((e for e in MOCK_ELECTIONS if e["country_iso2"].upper() == iso.upper()), None)
    
    if not election:
        raise HTTPException(status_code=404, detail="Election not found")
    
    # Count observations for this country
    country_obs = [o for o in MOCK_OBSERVATIONS if o.get("country_iso2") == iso.upper()]
    
    return {
        "metadata": {
            "id": election["id"],
            "country_iso2": election["country_iso2"],
            "country_name": election["country_name"],
            "date": election["election_date"],
            "type": election["election_type"],
            "status": election["status"]
        },
        "stats": {
            "total_alerts": len(country_obs) + 15,
            "critical_alerts": sum(1 for o in country_obs if o["severity"] == "CRITICO") + 2,
            "sentiment_score": 72
        }
    }

@app.get("/api/observations/latest")
def get_latest_observations(limit: int = 10):
    """Latest observations"""
    return MOCK_OBSERVATIONS[:limit]

@app.get("/api/reports")
def list_reports():
    """List available MOEP reports"""
    return [
        {"filename": "MOEP_UG_INTEGRAL.html", "path": "/reports/moep/MOEP_UG_INTEGRAL.html", "size_kb": 45.2, "type": "MOEP", "country_iso": "UG"},
        {"filename": "MOEP_NG_INTEGRAL.html", "path": "/reports/moep/MOEP_NG_INTEGRAL.html", "size_kb": 52.1, "type": "MOEP", "country_iso": "NG"},
        {"filename": "MOEP_CO_INTEGRAL.html", "path": "/reports/moep/MOEP_CO_INTEGRAL.html", "size_kb": 48.7, "type": "MOEP", "country_iso": "CO"},
        {"filename": "MOEP_CR_INTEGRAL.html", "path": "/reports/moep/MOEP_CR_INTEGRAL.html", "size_kb": 41.3, "type": "MOEP", "country_iso": "CR"},
    ]

@app.get("/health")
def health_check():
    """Health check for Railway"""
    return {"status": "healthy", "service": "democracia-api"}

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    print(f"🚀 Starting Democrac.IA API on port {port}...")
    uvicorn.run(app, host="0.0.0.0", port=port)
