# ASRP-Lab — High-Level Architecture

This document intentionally describes the project at a high level. Security-sensitive and proprietary implementation details are not published here.

## Conceptual architecture

```text
┌────────────────────────────────────────────┐
│                Web Interface               │
│ Researchers • Managers • Reviewers • Admin │
└──────────────────────┬─────────────────────┘
                       ▼
┌────────────────────────────────────────────┐
│              Application / API             │
│ Auth • Projects • Programs • Milestones    │
│ Teams • Budgets • Reporting • Audit        │
└──────────────────────┬─────────────────────┘
             ┌─────────┴─────────┐
             ▼                   ▼
┌──────────────────────┐  ┌──────────────────────┐
│ Structured Data      │  │ Documents / Evidence │
└──────────────────────┘  └──────────────────────┘
             │
             ▼
┌────────────────────────────────────────────┐
│       Analytics / Reporting Layer          │
└────────────────────────────────────────────┘
```

## Main logical domains

### Identity and access
Authentication, profiles, roles, permissions, organization membership, auditability.

### Research program management
Programs, projects, objectives, milestones, research teams, institutions, partners.

### Resource and budget monitoring
Budget tracking, resource allocation, cost visibility, planned vs. actual consumption.

### Results and evidence
Deliverables, publications, patents or innovation outputs where relevant, datasets, reports, measurable outcomes.

### Reporting and analytics
Dashboards, progress indicators, portfolio analysis, cross-program views, future AI-assisted analysis.

## Security principles

- least privilege;
- separation of duties;
- strong authentication for privileged users;
- encrypted communications;
- secure secret management;
- audit logging;
- data minimization;
- controlled document access;
- regular vulnerability review.

## Intentionally omitted

Production topology, credentials, private endpoints, complete database schema, proprietary algorithms, internal security rules, deployment secrets, and unpublished code modules.
