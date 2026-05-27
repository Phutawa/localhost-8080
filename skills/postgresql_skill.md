# PostgreSQL Database Management Skill

## Purpose
Guidelines for database migrations, query optimizations, and connection pooling.

## Best Practices
- Write raw SQL or utilize Prisma/migration tooling for database changes.
- Ensure all queries target optimized B-Tree or GIN indexes.
- Utilize database transaction blocks (ACID properties) for stateful updates.
