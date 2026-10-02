"""User persistence through an externally managed Session."""

from uuid import UUID

from sqlalchemy.orm import Session

from server.database.models import UserModel
from server.domain.entities import User


class SqlAlchemyUserRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, user: User) -> None:
        self._session.add(UserModel(id=user.id, created_at=user.created_at))

    def get_by_id(self, user_id: UUID) -> User | None:
        model = self._session.get(UserModel, user_id)
        if model is None:
            return None
        return User(id=model.id, created_at=model.created_at)
