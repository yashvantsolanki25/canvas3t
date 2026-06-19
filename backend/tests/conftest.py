import os
import tempfile

import pytest

from app import create_app
from app.extensions import db


@pytest.fixture()
def app():
    db_fd, db_path = tempfile.mkstemp()
    os.close(db_fd)
    os.environ["DATABASE_URL"] = f"sqlite:///{db_path}"

    app = create_app()
    app.config.update(TESTING=True)
    with app.app_context():
        db.create_all()
        try:
            yield app
        finally:
            db.session.remove()
            db.drop_all()
    os.unlink(db_path)


@pytest.fixture()
def client(app):
    return app.test_client()

