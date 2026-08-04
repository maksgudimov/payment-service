from types import TracebackType

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.payments.ports import DuplicateIdempotencyKeyError
from app.infrastructure.repositories import (
    SQLAlchemyOutboxRepository,
    SQLAlchemyPaymentRepository,
)


class SQLAlchemyPaymentUnitOfWork:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._committed = False
        self.payments = SQLAlchemyPaymentRepository(session)
        self.outbox = SQLAlchemyOutboxRepository(session)

    async def __aenter__(self) -> "SQLAlchemyPaymentUnitOfWork":
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        if exc_type is not None or not self._committed:
            await self._session.rollback()

    async def commit(self) -> None:
        try:
            await self._session.commit()
            self._committed = True
        except IntegrityError as error:
            await self._session.rollback()
            if self._is_idempotency_conflict(error):
                raise DuplicateIdempotencyKeyError from error
            raise

    @staticmethod
    def _is_idempotency_conflict(error: IntegrityError) -> bool:
        current: BaseException | None = error.orig
        while current is not None:
            constraint_name = getattr(current, "constraint_name", None)
            if constraint_name is None:
                constraint_name = getattr(
                    getattr(current, "diag", None), "constraint_name", None
                )
            if "idempotency_key" in (constraint_name or ""):
                return True
            current = current.__cause__ or current.__context__
        return False
