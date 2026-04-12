# 2. Architecture Constraints

## 2.1 Technical Constraints

| ID | Constraint | Reason |
|----|-----------|--------|
| TC-1 | Runtime: **Python 3.12** | Project tooling (Black, Ruff, isort, Bandit, pytest) is Python-based |
| TC-2 | Compute: **AWS Lambda** | Serverless-first principle; no self-hosted servers |
| TC-3 | API: **AWS API Gateway WebSocket** | Real-time push to both players without polling (ADR-003) |
| TC-4 | Database: **DynamoDB single-table** | Scales to zero, known access patterns (ADR-002) |
| TC-5 | Auth: **AWS Cognito** | Managed identity; JWT validation at the API layer |
| TC-6 | IaC: **AWS SAM / CloudFormation** | All resources defined in code; no manual console changes |

## 2.2 Organisational Constraints

| ID | Constraint | Reason |
|----|-----------|--------|
| OC-1 | Domain logic must be **infrastructure-free** | Enables fast unit tests without mocking AWS SDKs |
| OC-2 | One Lambda per action/event type | Single-responsibility principle; avoids monolithic handlers |
| OC-3 | No manual AWS console changes | Reproducibility and auditability of infrastructure |

## 2.3 Conventions

| ID | Convention |
|----|-----------|
| CV-1 | Game rules implemented as **pure functions** — same input always produces same output |
| CV-2 | All game actions modelled as **events** (e.g. `CardPlayed`, `TurnEnded`) |
| CV-3 | ADRs document every significant technology or design choice |
