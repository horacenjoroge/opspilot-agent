# Migration Strategy

Current status: Future Work

Database migrations are not implemented in the current repo. The app initializes SQLAlchemy tables directly at startup.

## Future Migration Plan

- choose a migration tool such as Alembic
- add revision creation workflow
- add upgrade and downgrade commands
- document safe migration sequencing

## Safe Migration Rules

- review schema diffs before applying
- avoid destructive changes without backups
- prefer additive changes first
- test migrations before deployment
