# CONN-STORY-001: Player Connects via WebSocket with JWT Auth

**Architecture Reference**: Section 6 — Runtime View, Scenario 1 (Player Connect & Matchmaking); Section 5.1 — Building Block View (ConnectFunction); Section 8.1 — Authentication & Authorisation
**Priority**: CORE
**Status**: TODO

---

## Original Story

AS A player
I WANT to open a WebSocket connection to the game server using my JWT token
SO THAT I am authenticated and my session is tracked, enabling me to join a game

### SCENARIO 1: Successful connection with valid JWT

**Scenario ID**: CONN-STORY-001-S1

**GIVEN**
* A registered Cognito user holds a valid JWT access token
* The WebSocket API endpoint is deployed and reachable

**WHEN**
* The player opens a WebSocket connection to `wss://<api-id>.execute-api.eu-central-1.amazonaws.com/prod?token=<JWT>`

**THEN**
* The connection is accepted (HTTP 101 Switching Protocols)
* A `CONN#<connectionId> → playerId` record is written to DynamoDB
* The player can send and receive WebSocket frames

### SCENARIO 2: Connection rejected with invalid JWT

**Scenario ID**: CONN-STORY-001-S2

**GIVEN**
* A client presents an expired or malformed JWT

**WHEN**
* The client attempts to open a WebSocket connection

**THEN**
* The connection is rejected with HTTP 401
* No DynamoDB record is written
* The rejection is logged in CloudWatch with the reason

---

## Frontend Sub-Stories

### CONN-FE-001.1: WebSocket connection lifecycle management

AS A player
I WANT the browser client to open, maintain, and reconnect the WebSocket connection automatically
SO THAT I stay connected to the game without manual intervention

#### SCENARIO 1: Client opens connection on page load

**Scenario ID**: CONN-FE-001.1-S1

**GIVEN**
* The player is logged in and holds a valid JWT in local storage
* The game page is loaded in the browser

**WHEN**
* The page initialises

**THEN**
* The client opens a WebSocket connection appending `?token=<JWT>` to the WSS URL
* The connection status indicator shows "Connected"

#### SCENARIO 2: Client displays error on rejected connection

**Scenario ID**: CONN-FE-001.1-S2

**GIVEN**
* The stored JWT is expired

**WHEN**
* The client attempts to connect

**THEN**
* The WebSocket `onerror` / `onclose` event fires
* The UI displays "Authentication failed — please log in again"
* The client does not attempt to reconnect automatically

---

## Backend Sub-Stories

### CONN-BE-001.1: ConnectFunction validates JWT and stores connection mapping

**Architecture Reference**: Section 5.1 — ConnectFunction; Section 8.1 — Authentication & Authorisation

AS A system
I WANT the ConnectFunction Lambda to validate the JWT via Cognito and persist the `connectionId → playerId` mapping
SO THAT subsequent Lambdas can identify which player owns a given connection

#### SCENARIO 1: Valid JWT stores connection record

**Scenario ID**: CONN-BE-001.1-S1

**GIVEN**
* A `$connect` event arrives with a valid JWT in `queryStringParameters.token`
* Cognito returns valid claims including `sub` (playerId)

**WHEN**
* ConnectFunction is invoked

**THEN**
* A DynamoDB item `PK=CONN#<connectionId>, SK=PLAYER` with `playerId` and TTL (+24 h) is written
* The function returns HTTP 200

#### SCENARIO 2: Invalid JWT returns 401 without writing to DynamoDB

**Scenario ID**: CONN-BE-001.1-S2

**GIVEN**
* A `$connect` event arrives with an expired JWT

**WHEN**
* ConnectFunction calls Cognito to validate the token

**THEN**
* Cognito returns an error
* The function returns HTTP 401
* No DynamoDB write is performed
* A structured warning log is emitted with `connectionId` and error reason

---

## Infrastructure Sub-Stories

### CONN-INFRA-001.1: Deploy ConnectFunction Lambda

**Architecture Reference**: Section 7.2 — Infrastructure as Code (ConnectFunction)

AS A DevOps engineer
I WANT the ConnectFunction Lambda deployed via SAM with the correct runtime and permissions
SO THAT the `$connect` WebSocket route has a compute target to invoke

#### SCENARIO 1: Lambda is deployed and invocable

**Scenario ID**: CONN-INFRA-001.1-S1

**GIVEN**
* `template.yaml` defines `ConnectFunction` with `Runtime: python3.12` and the `$connect` route integration

**WHEN**
* `sam deploy` completes successfully

**THEN**
* The Lambda function exists in the AWS account
* A manual `aws lambda invoke` with a synthetic `$connect` payload returns a 200 response
* The function appears in CloudWatch Logs with its log group

---

### CONN-INFRA-001.2: Provision DynamoDB table with connection access pattern

**Architecture Reference**: Section 5.3 — DynamoDB Access Patterns; Section 7.2 — Infrastructure as Code (GameTable)

AS A DevOps engineer
I WANT the DynamoDB single table deployed with the correct key schema and TTL enabled
SO THAT connection records can be stored and automatically expired after 24 hours

#### SCENARIO 1: Table exists with TTL enabled

**Scenario ID**: CONN-INFRA-001.2-S1

**GIVEN**
* `template.yaml` defines `GameTable` with `BillingMode: PAY_PER_REQUEST`, `PK` (HASH) and `SK` (RANGE) keys, and TTL attribute `ttl`

**WHEN**
* `sam deploy` completes

**THEN**
* The DynamoDB table exists in `eu-central-1`
* TTL is enabled on the `ttl` attribute
* A `PutItem` with `PK=CONN#test, SK=PLAYER` succeeds

---

### CONN-INFRA-001.3: Wire `$connect` route on WebSocket API Gateway

**Architecture Reference**: Section 5.1 — API Gateway; Section 7.2 — Infrastructure as Code (WebSocketApi)

AS A DevOps engineer
I WANT the WebSocket API Gateway `$connect` route integrated with ConnectFunction
SO THAT incoming WebSocket handshakes trigger the authentication Lambda

#### SCENARIO 1: `$connect` route delivers event to Lambda

**Scenario ID**: CONN-INFRA-001.3-S1

**GIVEN**
* `template.yaml` defines `WebSocketApi` with a `$connect` route pointing to `ConnectFunction`
* The stack is deployed

**WHEN**
* A WebSocket client connects to the API endpoint with a valid JWT

**THEN**
* API Gateway invokes `ConnectFunction` with a `$connect` event containing `connectionId` and `queryStringParameters`
* The Lambda returns HTTP 200 and the WebSocket handshake completes

---

### CONN-INFRA-001.4: CloudWatch alarm and structured logging for ConnectFunction

**Architecture Reference**: Section 8.3 — Logging & Observability; Section 10.1 — Quality Tree (Operability)

AS A DevOps engineer
I WANT ConnectFunction to emit structured JSON logs and have a CloudWatch alarm on errors
SO THAT authentication failures are observable and on-call engineers are alerted within 30 seconds

#### SCENARIO 1: Structured log emitted on every invocation

**Scenario ID**: CONN-INFRA-001.4-S1

**GIVEN**
* ConnectFunction uses AWS Lambda Powertools `Logger`
* A `$connect` event is processed (success or failure)

**WHEN**
* The Lambda completes execution

**THEN**
* A JSON log entry appears in `/aws/lambda/ConnectFunction` containing `connectionId`, `playerId` (or error reason), and `durationMs`

#### SCENARIO 2: CloudWatch alarm triggers on Lambda errors

**Scenario ID**: CONN-INFRA-001.4-S2

**GIVEN**
* A CloudWatch alarm is defined on the `Errors` metric for `ConnectFunction` with threshold ≥ 1 over 1 minute

**WHEN**
* ConnectFunction throws an unhandled exception

**THEN**
* The alarm transitions to `ALARM` state within 60 seconds
* The error and stack trace are visible in CloudWatch Logs

---

## Implementation Order

```
CONN-INFRA-001.2 (DynamoDB table)
  → CONN-INFRA-001.1 (Lambda deploy)
  → CONN-INFRA-001.3 ($connect route)
  → CONN-INFRA-001.4 (monitoring)
  → CONN-BE-001.1 (ConnectFunction logic)
  → CONN-FE-001.1 (client WebSocket lifecycle)
  → CONN-STORY-001 (E2E: connect with JWT, verify DynamoDB record)
```
