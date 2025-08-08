# Database Migrations

This directory contains database migration scripts for Synapse AI.

## Files

- `001_initial_schema.sql` - Initial PostgreSQL database schema
- `migrate.py` - Python migration script that handles both SQLite and PostgreSQL
- `README.md` - This file

## Usage

### Automatic Migration (Recommended)

The application automatically creates the database schema on startup. No manual migration is needed for basic usage.

### Manual Migration

For production deployments or when you need more control:

```bash
# Check database status
python migrations/migrate.py --check

# Run migration (safe - won't overwrite existing data)
python migrations/migrate.py

# Force re-run migration (caution - may affect existing data)
python migrations/migrate.py --force
```

## Database Configuration

### Development (SQLite)
Set in `.env`:
```
DATABASE_URL=sqlite:///./synapse_ai.db
```

### Production (PostgreSQL)
Set in `.env`:
```
DATABASE_URL=postgresql://username:password@host:port/database_name
```

## Migration Process

1. **SQLite**: Uses SQLAlchemy to create tables automatically
2. **PostgreSQL**: 
   - Creates database if it doesn't exist
   - Runs SQL migration script for optimal schema
   - Sets up indexes and triggers for performance

## Prerequisites

For PostgreSQL support:
```bash
pip install psycopg2-binary
```

## Schema Features

- **Auto-timestamps**: `created_at` and `updated_at` fields with triggers
- **Indexes**: Optimized indexes for common queries
- **Foreign Keys**: Proper relationships with cascade deletes
- **JSON Support**: JSONB fields for flexible metadata storage
- **Constraints**: Data validation at database level

## Security Notes

- Default admin user creation is commented out in production
- Adjust database user permissions as needed
- Use strong passwords for production databases
- Enable SSL for production PostgreSQL connections