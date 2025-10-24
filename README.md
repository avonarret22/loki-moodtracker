# Loki Moodtracker

Repositorio base para el desarrollo del asistente emocional conversacional *Loki*.  
Incluye la estructura inicial de servicios y configuracion minima para comenzar el MVP.

## Arquitectura Inicial

- **backend/**: API en FastAPI que orquesta WhatsApp, IA y logica de negocio.
- **frontend/**: espacio reservado para el dashboard web (React/Next.js sugerido).
- **docs/**: documentacion funcional y tecnica (ej. `modelo.txt`).
- **infrastructure/**: configuraciones futuras de despliegue/infra adicional.

## Requisitos Previos

- Docker y docker-compose para levantar backend + Postgres.
- Python 3.11+ si deseas ejecutar el backend sin contenedor.
- Cuenta/credenciales para WhatsApp Business, OpenAI y/o Anthropic segun integraciones.

## Primeros Pasos

```bash
cp .env.example .env
cp backend/.env.example backend/.env
docker-compose up --build
```

La API quedara disponible en `http://localhost:8000/health/`.

## Ambiente Local sin Docker

```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

## Proximos pasos sugeridos

1. Implementar migraciones (Alembic) y modelos de datos segun `modelo.txt`.
2. Conectar el webhook de WhatsApp y crear capa de mensajeria.
3. Disenar pruebas end-to-end para los flujos de check-in y reporte semanal.
