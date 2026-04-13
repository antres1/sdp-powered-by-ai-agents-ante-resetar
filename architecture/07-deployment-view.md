# 7. Deployment View

See [`diagrams/deployment.svg`](diagrams/deployment.svg).

## 7.1 Infrastructure Overview

All resources live in a single AWS region (`eu-central-1`). There are no servers
to manage — every compute unit is a Lambda function invoked on demand.

| Layer | Service | Notes |
|-------|---------|-------|
| Client | Browser | Static files served from S3 + CloudFront (or local dev server) |
| API | API Gateway WebSocket | Single stage (`prod`); routes map 1-to-1 to Lambdas |
| Auth | Cognito User Pool | JWT validated on `$connect`; no per-request auth overhead |
| Compute | AWS Lambda (×5) | Python 3.12, 128 MB memory, default 3s timeout |
| Storage | DynamoDB on-demand | Single table; TTL on connection items (24 h) |

## 7.2 Infrastructure as Code

All resources are defined in a SAM template (`template.yaml`):

```
template.yaml
├── WebSocketApi          (AWS::ApiGatewayV2::Api)
├── ConnectFunction       (AWS::Serverless::Function)
├── DisconnectFunction    (AWS::Serverless::Function)
├── MatchmakingFunction   (AWS::Serverless::Function)
├── PlayCardFunction      (AWS::Serverless::Function)
├── EndTurnFunction       (AWS::Serverless::Function)
├── GameTable             (AWS::DynamoDB::Table)
└── CognitoUserPool       (AWS::Cognito::UserPool)
```

## 7.3 Deployment Pipeline

```
git push → CI (GitHub Actions)
  → pytest (unit + integration)
  → sam build
  → sam deploy --stack-name tcg-prod
```

No manual steps; the pipeline is the only path to production.
