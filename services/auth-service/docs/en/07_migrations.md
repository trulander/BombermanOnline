# 7. Managing Database Migrations

[![Russian](https://img.shields.io/badge/lang-Russian-blue)](../ru/07_migrations.md)

Alembic is used to manage database schema changes. The process of creating and applying migrations is automated with commands.

## Configuration

The main Alembic configuration file is `alembic.ini`. It is configured to work with the `app/alembic` directory.

## Creating a New Migration

When you make changes to the SQLAlchemy models in the `app/models` directory, Alembic can automatically generate a migration file reflecting these changes.

To do this, you can use the command from `app/manage.py`:

```bash
# Make sure your virtual environment is activated
python app/manage.py makemigrations --name "Brief description of the migration"
```

Or run the Alembic command directly:

```bash
alembic revision --autogenerate -m "Brief description of the migration"
```

A new file will be created in `app/alembic/versions/`.

## Applying Migrations

To apply all the latest migrations to the database, use the command:

```bash
python app/manage.py migrate
```

Or directly through Alembic:

```bash
alembic upgrade head
```

## Reverting Migrations

To revert the last applied migration:

```bash
alembic downgrade -1
```

To revert to a specific version, specify its hash:

```bash
alembic downgrade <revision_hash>
```

## Viewing Migration History

To see the entire migration history and the current database version:

```bash
alembic history --verbose
```

To see only the current active migration:

```bash
alembic current
```
