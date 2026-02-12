# Multi-Database Architecture Diagram

## System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                      WaveSignals Platform                        │
│                    (Deployed on Vercel)                          │
└─────────────────────────────────────────────────────────────────┘
                                 │
                                 │
                    ┌────────────┴────────────┐
                    │                         │
              ┌─────▼─────┐           ┌─────▼─────┐
              │   READ    │           │   WRITE   │
              │ Operations│           │ Operations│
              └─────┬─────┘           └─────┬─────┘
                    │                       │
                    │                       │
                    │                       ▼
                    │              ┌────────────────┐
                    │              │ PRIMARY DB     │
                    │              │ OLD_DATABASE   │
                    │              │ (WRITE ONLY)   │
                    │              └────────────────┘
                    │                       ▲
                    │                       │
                    ▼                       │
        ┌───────────────────────┐          │
        │   Fallback Chain      │          │
        │                       │          │
        │  ┌─────────────────┐ │          │
        │  │ 1. OLD_DATABASE │─┼──────────┘
        │  │    (Primary)    │ │   Writes go here
        │  └─────────────────┘ │
        │           │           │
        │           ▼           │
        │  ┌─────────────────┐ │
        │  │ 2. NEW_DATABASE │ │
        │  │    (Backup)     │ │
        │  └─────────────────┘ │
        │           │           │
        │           ▼           │
        │  ┌─────────────────┐ │
        │  │ 3. DATABASE_URL │ │
        │  │    (Tertiary)   │ │
        │  └─────────────────┘ │
        │           │           │
        │           ▼           │
        │  ┌─────────────────┐ │
        │  │ 4. posts.json   │ │
        │  │ (File Fallback) │ │
        │  └─────────────────┘ │
        │                       │
        └───────────────────────┘
```

## Request Flow

### GET /api/posts (Read Operation)

```
User Request
     │
     ▼
┌─────────────────┐
│ Vercel Function │
│  (posts.py)     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  db_multi.py    │
│ get_posts_with  │
│   _fallback()   │
└────────┬────────┘
         │
         ▼
    Try OLD_DATABASE_URL ───┐
         │                  │ Success
         │ Fail             ▼
         ▼              Return Posts
    Try NEW_DATABASE_URL    │
         │                  │
         │ Fail             │
         ▼                  │
    Try DATABASE_URL        │
         │                  │
         │ Fail             │
         ▼                  │
    Load posts.json         │
         │                  │
         ▼                  │
    Return Posts ───────────┘
         │
         ▼
┌─────────────────┐
│  JSON Response  │
│  + X-Data-Source│
└─────────────────┘
```

### POST /api/cron (Write Operation)

```
Cron Job (6 AM UTC)
     │
     ▼
┌─────────────────┐
│ Vercel Function │
│   (cron.py)     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  db_multi.py    │
│ get_primary_db  │
│ _connection()   │
└────────┬────────┘
         │
         ▼
    Connect to PRIMARY
    (OLD_DATABASE_URL)
         │
         │ Success
         ▼
┌─────────────────┐
│  Generate AI    │
│  Content (GROQ) │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  INSERT INTO    │
│  posts TABLE    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Return Success  │
│  + Post ID      │
└─────────────────┘
```

## Database Priority Matrix

| Operation Type | Priority 1       | Priority 2       | Priority 3       | Priority 4    |
|----------------|------------------|------------------|------------------|---------------|
| **READ**       | OLD_DATABASE_URL | NEW_DATABASE_URL | DATABASE_URL     | posts.json    |
| **WRITE**      | OLD_DATABASE_URL | ❌ Fail          | ❌ Fail          | ❌ Fail       |

## Component Responsibilities

### `/api/db_multi.py` (Connection Manager)

```python
Functions:
├─ get_multi_db_connection()     # For READ operations
│  └─ Returns: (connection, source_name)
│
├─ get_primary_db_connection()   # For WRITE operations
│  └─ Returns: connection (OLD_DB only)
│
├─ get_posts_with_fallback()     # High-level read
│  └─ Returns: (posts[], source)
│
└─ get_single_post_with_fallback() # Single post read
   └─ Returns: (post{}, source)
```

### API Endpoints Using Multi-DB

```
/api/posts.py       → Uses: get_posts_with_fallback()
/api/post.py        → Uses: get_single_post_with_fallback()
/api/health.py      → Uses: get_multi_db_connection()
/api/cron.py        → Uses: get_primary_db_connection() (writes)
/api/subscribers.py → Uses: get_primary_db_connection() (writes)
```

## Data Consistency Model

```
┌───────────────────────────────────────────┐
│        Eventual Consistency Model         │
├───────────────────────────────────────────┤
│                                           │
│  PRIMARY DB (OLD_DATABASE_URL)            │
│    ▲                                      │
│    │ All writes go here                  │
│    │                                      │
│  ┌─┴─────────────────────────────────┐   │
│  │  Single Source of Truth           │   │
│  │  • New posts                      │   │
│  │  • Subscribers                    │   │
│  │  • Settings                       │   │
│  └───────────────────────────────────┘   │
│                                           │
│  BACKUP DBs are READ-ONLY                 │
│    • Snapshots/replicas                   │
│    • May be slightly out of sync          │
│    • Used only when primary fails         │
│                                           │
└───────────────────────────────────────────┘
```

## Failover Scenarios

### Scenario 1: Primary Database Down

```
User Request → OLD_DB (fails) → NEW_DB (success) → Response
                                                   
Header: X-Data-Source: new_db
Status: ⚠️ Degraded (reads only, writes will fail)
```

### Scenario 2: All Databases Down

```
User Request → OLD_DB (fails) → NEW_DB (fails) → DATABASE_URL (fails) 
                                                → posts.json (success)
                                                
Header: X-Data-Source: json_fallback
Status: 🔴 Critical (reads only from file, writes fail)
```

### Scenario 3: Normal Operation

```
User Request → OLD_DB (success) → Response

Header: X-Data-Source: old_db
Status: ✅ Healthy (reads and writes working)
```

## Monitoring Dashboard View

```
┌──────────────────────────────────────────────────────┐
│  WaveSignals Health Status                           │
├──────────────────────────────────────────────────────┤
│                                                      │
│  Database Status                                     │
│  ┌────────────────────────────────────────────┐     │
│  │ ● OLD_DATABASE    [Connected] ✅            │     │
│  │ ● NEW_DATABASE    [Standby]   ⏸            │     │
│  │ ● JSON Fallback   [Available] 📁            │     │
│  └────────────────────────────────────────────┘     │
│                                                      │
│  Current Data Source: old_db                         │
│  Total Posts: 150                                    │
│  Posts (24h): 1                                      │
│  Last Post: "How AI is Changing Tech" (2h ago)      │
│                                                      │
│  Cron Job Status                                     │
│  ┌────────────────────────────────────────────┐     │
│  │ Next Run: Today at 06:00 UTC (4h 23m)      │     │
│  │ Last Success: Yesterday 06:00 UTC           │     │
│  │ Success Rate: 98.5%                         │     │
│  └────────────────────────────────────────────┘     │
│                                                      │
└──────────────────────────────────────────────────────┘
```

## Environment Variable Hierarchy

```
Priority for READS:
1. OLD_DATABASE_URL ────► Your blog posts database (primary)
2. NEW_DATABASE_URL ────► Backup/replica database
3. DATABASE_URL    ────► Legacy fallback
4. posts.json      ────► Static file emergency fallback

Priority for WRITES:
1. OLD_DATABASE_URL ────► Only destination for writes
   └─ If fails: Write operation fails (no fallback)
```

## Benefits Visualization

```
          Single Database                Multi-Database
              (Old)                         (New)

    ┌────────────────┐              ┌────────────────┐
    │   DATABASE     │              │  OLD_DATABASE  │
    │                │              │   (Primary)    │
    └────────┬───────┘              └────────┬───────┘
             │                               │
    If fails │                      If fails │
             ▼                               ▼
    ┌────────────────┐              ┌────────────────┐
    │   ❌ ERROR     │              │  NEW_DATABASE  │
    │   Site Down    │              │   (Backup)     │
    └────────────────┘              └────────┬───────┘
                                             │
                                    If fails │
                                             ▼
                                    ┌────────────────┐
                                    │  posts.json    │
                                    │  (File Cache)  │
                                    └────────┬───────┘
                                             │
                                             ▼
                                    ┌────────────────┐
                                    │  ✅ Site Works │
                                    │  (Degraded)    │
                                    └────────────────┘

Uptime: 99.0%                       Uptime: 99.9%+
```

---

## Legend

```
Symbol  Meaning
──────  ─────────────────────────────────────
  ✅    Fully operational
  ⚠️    Degraded (reads only)
  🔴    Critical (file fallback)
  ❌    Failed/unavailable
  ⏸     Standby (not in use)
  ▶     Active connection
  →     Data flow
  │     Connection path
```

---

**Architecture Version:** 3.1-multi-db  
**Last Updated:** February 6, 2026
