"""Seed deterministic data for the connection lifetime experiments.

This script creates a cohort of demo users and items so the FastAPI
endpoints have realistic work to perform during load tests.  It only touches
records whose email addresses start with ``experiment-di-inline`` so it can be
run safely alongside other development data.
"""

from __future__ import annotations

import argparse
import logging
from typing import Tuple

from sqlalchemy import func
from sqlmodel import Session, select

from app.core.db import engine
from app.core.security import get_password_hash
from app.models import Item, User

logger = logging.getLogger(__name__)

EXPERIMENT_EMAIL_PREFIX = "experiment-di-inline"
EMAIL_TEMPLATE = EXPERIMENT_EMAIL_PREFIX + "+{index:03d}@example.com"
PASSWORD_DEFAULT = "experiment-pass"


def purge_experiment_data(session: Session) -> int:
    """Remove any previously seeded experiment data."""

    users = session.exec(
        select(User).where(User.email.startswith(EXPERIMENT_EMAIL_PREFIX))
    ).all()

    if not users:
        return 0

    for user in users:
        session.delete(user)

    session.commit()
    return len(users)


def ensure_user(
    session: Session,
    email: str,
    password_hash: str,
    full_name: str,
) -> Tuple[User, bool]:
    existing = session.exec(select(User).where(User.email == email)).first()
    if existing:
        if existing.hashed_password != password_hash:
            existing.hashed_password = password_hash
        if existing.full_name != full_name:
            existing.full_name = full_name
        return existing, False

    user = User(
        email=email,
        hashed_password=password_hash,
        full_name=full_name,
        is_active=True,
        is_superuser=False,
    )
    session.add(user)
    session.flush()
    return user, True


def ensure_items(session: Session, user: User, target_count: int) -> int:
    existing_count_result = session.exec(
        select(func.count())
        .select_from(Item)
        .where(Item.owner_id == user.id)
    ).first()
    existing_count = int(existing_count_result or 0)

    to_create = max(target_count - existing_count, 0)
    if to_create == 0:
        return 0

    for offset in range(existing_count, existing_count + to_create):
        session.add(
            Item(
                title=f"experiment-item-{offset + 1}",
                description="Seeded for connection lifetime experiments",
                owner_id=user.id,
            )
        )
    return to_create


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--users",
        type=int,
        default=10,
        help="Number of experiment users to ensure exist",
    )
    parser.add_argument(
        "--items-per-user",
        type=int,
        default=25,
        help="Items to create per experiment user",
    )
    parser.add_argument(
        "--password",
        default=PASSWORD_DEFAULT,
        help="Plain-text password to assign to experiment users",
    )
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Remove previously seeded experiment data before inserting fresh rows",
    )
    return parser.parse_args()


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    args = parse_args()

    created_users = 0
    created_items = 0

    with Session(engine) as session:
        if args.reset:
            removed = purge_experiment_data(session)
            if removed:
                logger.info("Removed %s experiment users", removed)
            else:
                logger.info("No experiment users to remove")

        password_hash = get_password_hash(args.password)

        for index in range(args.users):
            email = EMAIL_TEMPLATE.format(index=index)
            user, was_created = ensure_user(
                session=session,
                email=email,
                password_hash=password_hash,
                full_name=f"Experiment User {index:03d}",
            )
            if was_created:
                created_users += 1
            created_items += ensure_items(session, user, args.items_per_user)

        session.commit()

    logger.info(
        "Seed complete. created_users=%s created_items=%s ensured_users=%s password=%s",
        created_users,
        created_items,
        args.users,
        args.password,
    )


if __name__ == "__main__":
    main()
