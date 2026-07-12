"""
tests/test_watchlist.py — CineLog

Tests for the watchlist service.
"""

from datetime import datetime, timedelta, timezone

import pytest

from app import create_app, db
from models import Film, User, WatchlistEntry
from services.collection_service import FilmNotFoundError
from services.watchlist_service import add_to_watchlist, get_watchlist


@pytest.fixture
def app():
    """Create an isolated test app with an in-memory database."""
    app = create_app(config={
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
    })
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def sample_user(app):
    """A user to use in tests."""
    with app.app_context():
        user = User(username="testuser", email="test@example.com")
        db.session.add(user)
        db.session.commit()
        return user.id


@pytest.fixture
def sample_film(app):
    """A film to use in tests."""
    with app.app_context():
        film = Film(title="Paddington 2", year=2017, genre="Comedy")
        db.session.add(film)
        db.session.commit()
        return film.id


def test_add_to_watchlist_creates_entry(app, sample_user, sample_film):
    """Adding a valid film UUID should persist a watchlist entry."""
    with app.app_context():
        entry = add_to_watchlist(user_id=sample_user, film_id=sample_film)

        assert entry.user_id == sample_user
        assert entry.film_id == sample_film
        assert WatchlistEntry.query.filter_by(
            user_id=sample_user, film_id=sample_film
        ).count() == 1


def test_add_to_watchlist_nonexistent_film_raises(app, sample_user):
    """
    Adding a film_id that doesn't exist in the database should raise
    FilmNotFoundError, not a database integrity error.
    """
    with app.app_context():
        fake_film_id = "00000000-0000-0000-0000-000000000000"

        with pytest.raises(FilmNotFoundError):
            add_to_watchlist(user_id=sample_user, film_id=fake_film_id)


def test_get_watchlist_returns_newest_first(app, sample_user):
    """Watchlist results should include films with newest additions first."""
    with app.app_context():
        older_film = Film(title="Zulu")
        newer_film = Film(title="Alien")
        db.session.add_all([older_film, newer_film])
        db.session.flush()

        now = datetime.now(timezone.utc)
        db.session.add_all([
            WatchlistEntry(
                user_id=sample_user,
                film_id=older_film.id,
                date_added=now - timedelta(days=1),
            ),
            WatchlistEntry(
                user_id=sample_user,
                film_id=newer_film.id,
                date_added=now,
            ),
        ])
        db.session.commit()

        films = get_watchlist(sample_user)

        assert [film["id"] for film in films] == [newer_film.id, older_film.id]
