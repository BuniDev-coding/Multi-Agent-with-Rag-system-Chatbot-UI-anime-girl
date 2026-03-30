---
name: tech-research-architect
description: "Deep technical research and system architecture design. Covers technology evaluation, trade-off analysis, architecture patterns (microservices, monolith, serverless, event-driven), API design, database selection, scalability strategies, and proof-of-concept design. Use when comparing technologies, designing system architecture, evaluating technical feasibility, or solving complex engineering challenges."
license: MIT
version: 1.0.0
metadata:
  author: rd-agent
---

# Tech Research & Architecture

Expert-level technical research and system design. Use this skill to evaluate technologies, design architectures, and solve complex engineering problems with structured analysis.

## When to Use

- User asks "what is the best way to..." or "how does X work"
- Comparing technologies or frameworks (e.g. REST vs GraphQL, SQL vs NoSQL)
- Designing system architecture for a new product or feature
- Evaluating technical feasibility of a proposal
- Solving complex backend, infra, or integration challenges
- Investigating root causes of performance or scaling issues

## How It Works

1. **Understand the problem space** — clarify constraints (scale, team size, budget, timeline)
2. **Research options** — identify 2–4 candidate solutions with known trade-offs
3. **Evaluate trade-offs** — score options against requirements (performance, maintainability, cost, complexity)
4. **Recommend with reasoning** — pick the best fit and explain why alternatives were ruled out
5. **Provide proof-of-concept** — show a minimal architecture diagram or code sketch when helpful

## Architecture Patterns

### Choose Based on Scale & Team

| Pattern | Best For | Avoid When |
|---------|---------|------------|
| **Monolith** | Early-stage, small team, fast iteration | Team > 10 engineers, independent scaling needed |
| **Microservices** | Independent scaling, large teams, clear domain boundaries | Small team, unclear domains, high ops overhead |
| **Serverless** | Event-driven, variable load, minimal ops | Long-running tasks, low-latency requirements |
| **Event-Driven** | Async workflows, decoupled systems, audit trails | Simple CRUD, real-time sync required |

## Technology Evaluation Framework

When comparing technologies, evaluate across these dimensions:

```
1. Performance       — throughput, latency, resource usage
2. Developer UX      — learning curve, tooling, community
3. Operational cost  — hosting, maintenance, observability
4. Scalability       — horizontal/vertical, data volume limits
5. Ecosystem fit     — integrations, language compatibility
6. Maturity & risk   — stability, vendor lock-in, longevity
```

## Database Selection Guide

| Use Case | Recommendation | Why |
|----------|---------------|-----|
| Relational data, transactions | PostgreSQL | ACID, JSON support, mature |
| Simple key-value / cache | Redis | In-memory, pub/sub, TTL |
| Document store, flexible schema | MongoDB | Schema-less, horizontal scale |
| Time-series / metrics | InfluxDB / TimescaleDB | Optimized for time queries |
| Full-text search | Elasticsearch | Inverted index, aggregations |
| Graph relationships | Neo4j | Native graph traversal |

## API Design Principles

- **REST**: Use for standard CRUD resources; follow HTTP semantics (GET/POST/PUT/DELETE)
- **GraphQL**: Use when clients need flexible queries or multiple resource types in one call
- **gRPC**: Use for internal service-to-service communication requiring high throughput
- **WebSocket**: Use for real-time bidirectional communication (chat, live updates)

## Common Anti-Patterns to Avoid

- **Premature microservices** — splitting before domain boundaries are clear
- **Over-engineering** — using distributed systems for a 100-user app
- **Ignoring operational cost** — choosing tech without considering deployment/monitoring complexity
- **Resume-driven architecture** — picking trendy tech instead of proven solutions

## Output Format

Always structure technical recommendations as:

```
## Recommendation: [chosen solution]

**Why:** [2-3 sentence justification]

**Trade-offs accepted:**
- [what we gain]
- [what we give up]

**Alternatives considered:**
- [Option A] — ruled out because [reason]
- [Option B] — ruled out because [reason]

**Next step:** [concrete action to validate or implement]
```
