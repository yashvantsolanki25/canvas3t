from __future__ import annotations

import click
from flask.cli import with_appcontext

from app import create_app
from app.extensions import db

app = create_app()


@click.command("init-db")
@with_appcontext
def init_db_command():
    """Create database tables."""
    db.create_all()
    click.echo("Database initialized.")


app.cli.add_command(init_db_command)

