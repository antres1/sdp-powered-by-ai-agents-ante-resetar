# 1. Introduction and Goals

## 1.1 Purpose

This document describes the architecture of the **Trading Card Game (TCG)** — a
turn-based multiplayer card game implemented as a single Python service running
in a local Docker container.

The game is based on the
[Trading Card Game Kata](https://codingdojo.org/kata/TradingCardGame/) and
implements its full rule set:

- Each player starts with **30 Health** and **0 Mana slots**.
- Players draw from a 20-card deck (cards cost 0–8 mana).
- Each turn: refill mana, draw a card, play any affordable cards, end turn.
- A card played deals damage equal to its mana cost.
- **Bleeding Out**: drawing from an empty deck deals 1 damage.
- **Overload**: drawing a card when hand is full (5 cards) discards it.
- A player reduced to 0 or fewer Health loses.

---

## 1.2 Quality Goals

| Priority | Quality Goal | Motivation |
|----------|-------------|------------|
| 1 | **Correctness** | Game rules must be enforced exactly — wrong state transitions break the game |
| 2 | **Responsiveness** | A game action and its broadcast to both players completes within ~500 ms |
| 3 | **Testability** | Domain logic must be fully unit-testable without any infrastructure |
| 4 | **Reproducibility** | `docker build && docker run` must be the only path to a working system |
| 5 | **Operability** | Observable via container logs; no external services required |

---

## 1.3 Stakeholders

| Role | Expectation |
|------|-------------|
| **Player** | Fair, responsive gameplay; no lost game state |
| **Developer** | Clean domain model, fast test feedback, one-command local run |
| **Operator** | Single container to start and stop; logs visible via `docker logs` |
