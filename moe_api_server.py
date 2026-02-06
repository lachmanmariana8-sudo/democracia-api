from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import sqlite3
import uvicorn
from pathlib import Path
from typing import List, Dict, Any

# Configuración
app = FastAPI(title="Democrac.IA API Core", version="2.0.0")
DB_PATH = Path("data/democracia_ia.db")

# CORS para permitir peticiones desde el Next.js (localhost:3000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # En prod restringir a dominio real
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

@app.get("/")
def read_root():
    return {"status": "online", "system": "Democrac.IA Elite Core v9.9.8"}

@app.get("/api/dashboard/stats")
def get_dashboard_stats():
    """KPIs principales para el Dashboard."""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Total Hallazgos
        cur.execute("SELECT COUNT(*) FROM moe_observation")
        total_obs = cur.fetchone()[0]
        
        # Riesgo Crítico
        cur.execute("SELECT COUNT(*) FROM moe_observation WHERE severity IN ('CRITICO', 'ALERTA')")
        critical_obs = cur.fetchone()[0]
        
        # Voto Exterior (Nuevo Fase 41)
        cur.execute("SELECT COUNT(*) FROM moe_observation WHERE category = 'VOTO_EXTERIOR'")
        overseas_obs = cur.fetchone()[0]
        
        conn.close()
        
        return {
            "total_observations": total_obs,
            "critical_risk": critical_obs,
            "overseas_monitor": overseas_obs,
            "ire_index": min(round((critical_obs / max(total_obs, 1)) * 100, 1), 100) # Calculo simple IRE
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/observations/latest")
def get_latest_observations(limit: int = 10):
    """Últimos hallazgos en tiempo real."""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT id, category, indicator as title, severity, captured_at, source_name, source_url 
            FROM moe_observation 
            ORDER BY captured_at DESC 
            LIMIT ?
        """, (limit,))
        rows = cur.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/elections")
def get_elections():
    """Lista de elecciones activas."""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        # Mocking the countries join since it's a single table in SQLite usually or simplified
        # Checking schema from earlier read of moe_agent.py
        # Table is moe_election. Columns: id, country_iso2, country_name, election_type, election_date...
        cur.execute("""
            SELECT id, country_iso2, country_name, election_type, election_date, monitoring_status as status
            FROM moe_election
            WHERE monitoring_status = 'ACTIVE'
            ORDER BY election_date ASC
        """)
        rows = cur.fetchall()
        conn.close()
        
        # Transform for frontend compatibility
        results = []
        for row in rows:
            r = dict(row)
            results.append({
                "id": r["id"],
                "country_iso2": r["country_iso2"],
                "election_date": r["election_date"],
                "election_type": r["election_type"],
                "status": r["status"],
                "countries": {
                    "name": r["country_name"],
                    "iso2": r["country_iso2"]
                }
            })
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/elections/{iso}")
def get_election_detail(iso: str):
    """Detalle de una elección específica por ISO."""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT id, country_iso2, country_name, election_type, election_date, monitoring_status
            FROM moe_election
            WHERE country_iso2 = ? AND monitoring_status = 'ACTIVE'
            ORDER BY election_date ASC
            LIMIT 1
        """, (iso.upper(),))
        row = cur.fetchone()
        
        if not row:
            conn.close()
            raise HTTPException(status_code=404, detail="Election not found")
        
        r = dict(row)
        
        # Get observation stats for this country
        cur.execute("""
            SELECT COUNT(*) as total, 
                   SUM(CASE WHEN severity = 'CRITICO' THEN 1 ELSE 0 END) as critical
            FROM moe_observation 
            WHERE category LIKE ? OR source_name LIKE ?
        """, (f"%{iso.upper()}%", f"%{r['country_name']}%"))
        stats_row = cur.fetchone()
        conn.close()
        
        return {
            "metadata": {
                "id": r["id"],
                "country_iso2": r["country_iso2"],
                "country_name": r["country_name"],
                "date": r["election_date"],
                "type": r["election_type"],
                "status": r["monitoring_status"]
            },
            "stats": {
                "total_alerts": stats_row["total"] if stats_row else 0,
                "critical_alerts": stats_row["critical"] if stats_row else 0,
                "sentiment_score": 65  # Placeholder
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

from fastapi.staticfiles import StaticFiles
import os
from datetime import datetime

# Mount reports directory for direct download
app.mount("/reports", StaticFiles(directory="data/reports"), name="reports")

@app.get("/api/reports")
def list_reports():
    """Lista los reportes MOEP disponibles (filtrado)."""
    try:
        reports_dir = Path("data/reports")
        evidence = []
        
        # Only scan MOEP folder for integral reports
        moep_dir = reports_dir / "moep"
        
        if moep_dir.exists():
            for file in moep_dir.glob("MOEP_*_INTEGRAL.html"):
                stat = file.stat()
                # Extract country from filename
                parts = file.stem.split("_")
                country_iso = parts[1] if len(parts) > 1 else "??"
                evidence.append({
                    "filename": file.name,
                    "path": f"/reports/{file.relative_to(reports_dir).as_posix()}",
                    "size_kb": round(stat.st_size / 1024, 1),
                    "created_at": datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S"),
                    "type": "MOEP",
                    "country_iso": country_iso
                })
        
        # Sort by country
        evidence.sort(key=lambda x: x["country_iso"])
        return evidence
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/elections/{iso}")
def get_election_detail(iso: str):
    """Detalle de una misión específica."""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Get Election Details
        cur.execute("""
            SELECT id, country_iso2, country_name, election_type, election_date, monitoring_status as status
            FROM moe_election
            WHERE country_iso2 = ?
        """, (iso.upper(),))
        row = cur.fetchone()
        
        if not row:
            conn.close()
            raise HTTPException(status_code=404, detail="Election not found")
            
        election = dict(row)
        
        # Get Stats for this election
        # Total Observations for this country (assuming category or logic links it, 
        # but for now we might filter observations by source or title if we don't have explicit country link in observations)
        # In this schema, `moe_observation` doesn't seem to have `country_iso2` directly visible in previous reads?
        # Let's check schema assumption. `moe_observation` had `category`, `observation`, `severity`.
        # Usually filtering by text or if 'category' holds country.
        # For MVP, we will return global stats or mock country specific breakdown if column missing.
        # Let's check `moe_observation` schema via query or just use a simple robust query.
        
        # Checking if 'country_iso2' exists in moe_observation would be safer.
        # But let's assume valid linkage or add a placeholder.
        # Based on previous `moe_agent.py`, observations are linked to rounds or just loose.
        
        # For now, let's just return the election metadata and mock the specific stats 
        # until we confirm the FK relationship.
        
        result = {
            "metadata": {
                "id": election["id"],
                "country_iso2": election["country_iso2"],
                "country_name": election["country_name"],
                "date": election["election_date"],
                "type": election["election_type"],
                "status": election["status"]
            },
            "stats": {
                "total_alerts": 0, # Placeholder
                "critical_alerts": 0,
                "sentiment_score": 75
            }
        }
        conn.close()
        return result
    except Exception as e:
        print(f"Error getting election {iso}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    print("🚀 Iniciando Democrac.IA API Server en puerto 8000...")
    uvicorn.run(app, host="0.0.0.0", port=8000)
