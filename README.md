# QuantumShield

> **Quantum-Assisted Cybersecurity Platform** — Advanced security monitoring, quantum state verification, and authorized attack simulation in an isolated sandbox environment.

---

## ⚠️ Scientific & Security Disclaimer

- **Simulation Only:** All quantum computations are executed via Qiskit Aer classical simulation. No physical quantum hardware is currently connected.
- **Additive Verification:** Quantum-assisted verification (QVE) is strictly an additive evaluation layer. It never overrides classical rejections and does not claim to secure classical HTTP transport or relational databases.
- **Strict Sandbox Boundary:** The Attack Lab targets only registered, isolated local sandboxes with synthetic data. No external or production systems are targeted.
- **Development Status:** This repository contains the Day 2 runnable foundation.

---

## Repository Structure

```text
quantumshield/
├── apps/
│   ├── defender-web/          # Next.js 15 Operator Dashboard (Port 3000)
│   └── attack-lab-web/        # Next.js 15 Attack Simulation Lab (Port 3001)
├── packages/
│   ├── api-client/            # Shared TypeScript API client
│   └── ui/                    # Shared UI primitives
├── backend/
│   ├── api/                   # FastAPI application, routers, middleware
│   ├── common/                # Shared enums, settings, errors, logging
│   ├── quantum_engine/        # Qiskit circuits, backends, noise models, verification
│   ├── attack_engine/         # Isolated attack scenarios & safety interlocks
│   ├── detection/             # Rule-based and anomaly detection engines
│   ├── response/              # Policy-driven automated response handling
│   ├── evaluation/            # Detections vs ground-truth metrics & reports
│   └── workers/               # Asynchronous queue workers
├── infrastructure/
│   ├── docker/                # Container build specifications
│   └── database/              # PostgreSQL DDL and migration scripts
├── docs/                      # Approved project specifications & architecture
├── tests/
│   ├── unit/                  # Fast unit & endpoint tests
│   ├── integration/           # Integration tests
│   └── quantum/               # Circuit & quantum verification tests
├── docker-compose.yml
├── pytest.ini
├── .env.example
└── .gitignore
```

---

## Prerequisites

- **Node.js:** v18.0.0+ (v24.15.0 verified)
- **Python:** 3.11+ (3.14.3 verified)
- **Git:** 2.x+
- **Docker & Docker Compose** (optional for containerized services)

---

## Quickstart

### 1. Environment Setup

```bash
# Clone the repository
git clone https://github.com/dheerajpandita22/quantumshield.git
cd quantumshield

# Configure environment variables
cp .env.example .env
```

### 2. Backend (FastAPI)

```bash
# Install Python dependencies
pip install -r backend/requirements.txt

# Start the API server
python -m uvicorn backend.api.main:app --host 0.0.0.0 --port 8000 --reload
```
- API Docs (Swagger): http://localhost:8000/docs
- Health endpoint: http://localhost:8000/health

### 3. Frontend Applications

#### Defender Web (`localhost:3000`)
```bash
cd apps/defender-web
npm install
npm run dev
```

#### Attack Lab Web (`localhost:3001`)
```bash
cd apps/attack-lab-web
npm install
npm run dev
```

---

## Automated Testing

```bash
# Run all Python backend & quantum tests
pytest -v

# Run only unit/API health tests
pytest tests/unit/ -v

# Run quantum circuit tests
pytest tests/quantum/ -v
```

---

## Documentation

Full architectural specifications are available in the `docs/` directory:
- [System Architecture](docs/architecture/system-architecture.md)
- [Quantum Protocol Specification](docs/quantum/quantum-protocol-spec.md)
- [Hybrid Security Architecture](docs/security/hybrid-security-architecture.md)
- [Attack Lab Methodology](docs/security/attack-lab-methodology.md)
- [API Contracts & Enums](docs/api/api-contracts-and-schema.md)
- [Frontend Specification](docs/frontend/application-specification.md)
- [Testing Strategy](docs/testing/testing-strategy.md)
- [Detection & Evaluation](docs/evaluation/detection-and-evaluation.md)
- [Day 2 Baseline Report](docs/development/day-2-baseline-report.md)
- [Day 2 Completion Report](docs/development/day-2-completion-report.md)

---

## License

All rights reserved. Proprietary and confidential.
