# CONN-STORY-002: Player Disconnects Cleanly

**Architecture Reference**: Section 5.1 — Building Block View (DisconnectFunction); Section 8.5 — WebSocket Connection Lifecycle; Section 7.2 — Infrastructure as Code (DisconnectFunction)
**Priority**: SUPPORTING
**Status**: TODO

---

## Original Story

AS A player
I WANT my WebSocket connection record to be removed when I disconnect
SO THAT stale connection entries do not accumulate in DynamoDB and the system stays consistent

### SCENARIO 1: Clean disconnect removes connection record

**Scenario ID**: CONN-STORY-002-S1

**GIVEN**
* A `CONN#<connectionId> / PLAYER` item exists in DynamoDB
* The player closes the browser tab or the WebSocket connection drops

**WHEN**
* API Gateway fires the `$disconnect` event

**THEN**
* The `CONN#<connectionId> / PLAYER` item is deleted from DynamoDB
* No error is returned

### SCENARIO 2: Disconnect for unknown connectionId is a no-op

**Scenario ID**: CONN-STORY-002-S2

**GIVEN**
* No `CONN#<connectionId> / PLAYER` item exists (e.g. TTL already expired it)

**WHEN**
* DisconnectFunction is invoked with that `connectionId`

**THEN**
* The function completes without error (idempotent delete)
* A structured log entry records the missing item as a warning

---

## Frontend Sub-Stories

### CONN-FE-002.1: Client handles unexpected disconnection gracefully

AS A player
I WANT the UI to detect a dropped connection and show a reconnecting indicator
SO THAT I am not left staring at a frozen game board

#### SCENARIO 1: UI shows reconnecting state on unexpected close

**Scenario ID**: CONN-FE-002.1-S1

**GIVEN**
* The WebSocket connection is open and a game is in progress

**WHEN**
* The WebSocket `onclose` event fires unexpectedly (not a user-initiated action)

**THEN**
* The UI overlays a "Connection lost — reconnecting…" message
* Game board controls are disabled to prevent actions on a dead connection

---

## Backend Sub-Stories

### CONN-BE-002.1: DisconnectFunction deletes connection record

**Architecture Reference**: Section 5.1 — DisconnectFunction; Section 8.5 — WebSocket Connection Lifecycle

AS A system
I WANT DisconnectFunction to delete the `CONN#<connectionId>` item from DynamoDB on `$disconnect`
SO THAT stale connection mappings are removed promptly (TTL is a fallback, not the primary cleanup)

#### SCENARIO 1: Connection item deleted on disconnect

**Scenario ID**: CONN-BE-002.1-S1

**GIVEN**
* A `$disconnect` event arrives with a known `connectionId`

**WHEN**
* DisconnectFunction executes

**THEN**
* `DeleteItem` is called for `PK=CONN#<connectionId>, SK=PLAYER`
* The function returns HTTP 200

#### SCENARIO 2: GoneException from postToConnection handled in other Lambdas

**Scenario ID**: CONN-BE-002.1-S2

**GIVEN**
* A game-action Lambda calls `postToConnection` for a `connectionId` that has already disconnected

**WHEN**
* API Gateway Management API returns `GoneException`

**THEN**
* The Lambda catches `GoneException`, deletes the stale connection item, logs a warning, and does not fail the overall action (per Section 8.5)

---

## Infrastructure Sub-Stories

### CONN-INFRA-002.1: Deploy DisconnectFunction Lambda

**Architecture Reference**: Section 7.2 — Infrastructure as Code (DisconnectFunction)

AS A DevOps engineer
I WANT DisconnectFunction deployed via SAM with the `$disconnect` route integration
SO THAT WebSocket disconnections trigger the cleanup Lambda

#### SCENARIO 1: Lambda deployed and invocable

**Scenario ID**: CONN-INFRA-002.1-S1

**GIVEN**
* `template.yaml` defines `DisconnectFunction` with `Runtime: python3.12` and the `$disconnect` route

**WHEN**
* `sam deploy` completes

**THEN**
* The Lambda exists and a synthetic invocation returns without a 5xx error
* The log group `/aws/lambda/DisconnectFunction` exists

---

### CONN-INFRA-002.2: DynamoDB DeleteItem permission for DisconnectFunction

**Architecture Reference**: Section 5.3 — DynamoDB Access Patterns (Connection)

AS A DevOps engineer
I WANT DisconnectFunction's IAM role to allow `DeleteItem` on `GameTable`
SO THAT it can remove connection records on disconnect

#### SCENARIO 1: DeleteItem succeeds for DisconnectFunction role

**Scenario ID**: CONN-INFRA-002.2-S1

**GIVEN**
* DisconnectFunction's execution role has `dynamodb:DeleteItem` on `GameTable`
* A `CONN#<connectionId> / PLAYER` item exists

**WHEN**
* DisconnectFunction calls `DeleteItem`

**THEN**
* The item is removed without an `AccessDeniedException`

---

### CONN-INFRA-002.3: Wire `$disconnect` route on WebSocket API Gateway

**Architecture Reference**: Section 5.1 — API Gateway; Section 7.2 — Infrastructure as Code

AS A DevOps engineer
I WANT the `$disconnect` route integrated with DisconnectFunction
SO THAT all WebSocket disconnections trigger cleanup

#### SCENARIO 1: `$disconnect` route delivers event to Lambda

**Scenario ID**: CONN-INFRA-002.3-S1

**GIVEN**
* `template.yaml` defines a `$disconnect` route pointing to `DisconnectFunction`
* The stack is deployed

**WHEN**
* A WebSocket client disconnects

**THEN**
* API Gateway invokes `DisconnectFunction` with the `connectionId`

---

### CONN-INFRA-002.4: CloudWatch logging for DisconnectFunction

**Architecture Reference**: Section 8.3 — Logging & Observability

AS A DevOps engineer
I WANT DisconnectFunction to emit structured logs on every invocation
SO THAT disconnect events and stale-connection warnings are observable

#### SCENARIO 1: Structured log emitted on disconnect

**Scenario ID**: CONN-INFRA-002.4-S1

**GIVEN**
* DisconnectFunction uses AWS Lambda Powertools `Logger`

**WHEN**
* A `$disconnect` event is processed

**THEN**
* A JSON log entry appears in `/aws/lambda/DisconnectFunction` containing `connectionId` and `durationMs`

---

## Implementation Order

```
CONN-INFRA-002.2 (IAM DeleteItem — table already exists)
  → CONN-INFRA-002.1 (Lambda deploy)
  → CONN-INFRA-002.3 ($disconnect route)
  → CONN-INFRA-002.4 (logging)
  → CONN-BE-002.1 (DisconnectFunction logic + GoneException handling)
  → CONN-FE-002.1 (disconnection UI indicator)
  → CONN-STORY-002 (E2E: disconnect, verify DynamoDB record removed)
```
