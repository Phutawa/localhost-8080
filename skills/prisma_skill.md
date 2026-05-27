# Prisma ORM Integration Skill

## Purpose
Guidelines for schema design, migrations, and query execution with Prisma ORM.

## Best Practices
- Maintain a single source of truth in `schema.prisma`.
- Always generate migrations (`prisma migrate dev`) for database modifications.
- Optimize relation queries using `select` and `include` to avoid N+1 query problems.
