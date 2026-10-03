"""PostgreSQL integration checks for the first migration and repositories."""

from datetime import datetime, timezone
from importlib import import_module
from uuid import UUID, uuid4

import pytest
from alembic.operations import Operations
from alembic.autogenerate import compare_metadata
from alembic.runtime.migration import MigrationContext
from sqlalchemy import MetaData, create_engine, inspect, select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from server.config import get_settings
from server.database.models import CaptureModel, DeviceModel, UserModel
from server.database.repositories.capture import SqlAlchemyCaptureRepository
from server.database.repositories.device import SqlAlchemyDeviceRepository
from server.database.repositories.user import SqlAlchemyUserRepository
from server.database.session import Base
from server.domain.entities import Capture, Device, User
from server.domain.enums import ProcessingStatus
from server.services.capture_worker_service import CaptureWorkerService


@pytest.fixture
def database_session():
    """Apply the real migration in a disposable PostgreSQL schema."""
    engine = create_engine(get_settings().database_url)
    schema = f"test_domain_{uuid4().hex}"
    migration = import_module(
        "server.database.migrations.versions.0001_domain_persistence"
    )

    try:
        with engine.connect() as connection:
            connection.execute(text(f"CREATE SCHEMA {schema}"))
            connection.commit()
            connection.execute(text(f"SET search_path TO {schema}, public"))
            connection.commit()

            with Operations.context(MigrationContext.configure(connection)):
                migration.upgrade()
            connection.commit()

            try:
                with Session(connection, info={"test_schema": schema}) as session:
                    yield session
                    session.rollback()

                with Operations.context(MigrationContext.configure(connection)):
                    migration.downgrade()
                connection.commit()
                assert not {"users", "devices", "captures"} & set(
                    inspect(connection).get_table_names(schema=schema)
                )
            finally:
                connection.rollback()
                connection.execute(text(f"DROP SCHEMA {schema} CASCADE"))
                connection.commit()
    finally:
        engine.dispose()


def create_user_and_device(session: Session) -> tuple[UserModel, DeviceModel]:
    user = UserModel()
    session.add(user)
    session.flush()
    device = DeviceModel(user_id=user.id, name="Laptop")
    session.add(device)
    session.flush()
    return user, device


def test_persist_user_device_and_capture(database_session: Session) -> None:
    user, device = create_user_and_device(database_session)
    captured_at = datetime(2026, 10, 1, 8, 30, tzinfo=timezone.utc)
    capture = CaptureModel(device_id=device.id, captured_at=captured_at)
    database_session.add(capture)
    database_session.flush()
    database_session.expire_all()

    stored = database_session.scalars(
        select(CaptureModel).where(CaptureModel.id == capture.id)
    ).one()
    assert stored.device.user_id == user.id
    assert stored.captured_at == captured_at
    assert stored.created_at.tzinfo is not None
    assert stored.updated_at.tzinfo is not None
    assert device.created_at.tzinfo is not None
    assert user.created_at.tzinfo is not None


def test_device_requires_existing_user(database_session: Session) -> None:
    with pytest.raises(IntegrityError), database_session.begin_nested():
        database_session.add(DeviceModel(user_id=uuid4()))
        database_session.flush()


def test_capture_requires_existing_device(database_session: Session) -> None:
    with pytest.raises(IntegrityError), database_session.begin_nested():
        database_session.add(
            CaptureModel(device_id=uuid4(), captured_at=datetime.now(timezone.utc))
        )
        database_session.flush()


@pytest.mark.parametrize("table, required_column", [("devices", "user_id"), ("captures", "device_id")])
def test_relationship_foreign_keys_are_non_null(
    database_session: Session, table: str, required_column: str
) -> None:
    columns = {column["name"]: column for column in inspect(database_session.connection()).get_columns(table)}
    assert columns[required_column]["nullable"] is False


def test_capture_defaults_to_pending(database_session: Session) -> None:
    _, device = create_user_and_device(database_session)
    capture = CaptureModel(device_id=device.id, captured_at=datetime.now(timezone.utc))
    database_session.add(capture)
    database_session.flush()
    assert capture.processing_status == ProcessingStatus.PENDING

    status = database_session.execute(
        text("SELECT processing_status FROM captures WHERE id = :id"), {"id": capture.id}
    ).scalar_one()
    assert status == ProcessingStatus.PENDING

    database_default = database_session.execute(
        text("INSERT INTO captures (device_id, captured_at) "
             "VALUES (:device_id, :captured_at) RETURNING processing_status"),
        {"device_id": device.id, "captured_at": datetime.now(timezone.utc)},
    ).scalar_one()
    assert database_default == ProcessingStatus.PENDING


def test_database_rejects_invalid_processing_status(database_session: Session) -> None:
    _, device = create_user_and_device(database_session)
    with pytest.raises(IntegrityError), database_session.begin_nested():
        database_session.execute(
            text("INSERT INTO captures (device_id, captured_at, processing_status) "
                 "VALUES (:device_id, :captured_at, :status)"),
            {"device_id": device.id, "captured_at": datetime.now(timezone.utc),
             "status": "invalid"},
        )


def test_same_capture_timestamp_is_allowed(database_session: Session) -> None:
    _, device = create_user_and_device(database_session)
    captured_at = datetime(2026, 10, 1, 8, 30, tzinfo=timezone.utc)
    first = CaptureModel(device_id=device.id, captured_at=captured_at)
    second = CaptureModel(device_id=device.id, captured_at=captured_at)
    database_session.add_all([first, second])
    database_session.flush()
    assert first.id != second.id


def test_user_deletion_cascades_to_devices_and_captures(database_session: Session) -> None:
    user, device = create_user_and_device(database_session)
    capture = CaptureModel(device_id=device.id, captured_at=datetime.now(timezone.utc))
    database_session.add(capture)
    database_session.flush()

    database_session.execute(text("DELETE FROM users WHERE id = :id"), {"id": user.id})
    assert database_session.execute(text("SELECT count(*) FROM devices")).scalar_one() == 0
    assert database_session.execute(text("SELECT count(*) FROM captures")).scalar_one() == 0


def test_migration_matches_orm_metadata(database_session: Session) -> None:
    schema = database_session.info["test_schema"]
    connection = database_session.connection()
    assert set(inspect(connection).get_table_names(schema=schema)) == {
        "users", "devices", "captures"
    }

    schema_metadata = MetaData(schema=schema)
    for table in Base.metadata.sorted_tables:
        table.to_metadata(schema_metadata, schema=schema)

    context = MigrationContext.configure(
        connection,
        opts={
            "include_schemas": True,
            "include_name": lambda name, type_, parent_names: (
                name == schema if type_ == "schema" else True
            ),
        },
    )
    assert compare_metadata(context, schema_metadata) == []


def test_domain_timestamps_must_be_timezone_aware() -> None:
    aware = datetime.now(timezone.utc)
    user_id, device_id = uuid4(), uuid4()
    User(id=user_id, created_at=aware)
    Device(id=device_id, user_id=user_id, name=None, created_at=aware)
    Capture(
        id=uuid4(), device_id=device_id, captured_at=aware,
        processing_status=ProcessingStatus.PENDING, created_at=aware, updated_at=aware,
    )

    with pytest.raises(ValueError, match="captured_at must be timezone-aware"):
        Capture(
            id=uuid4(), device_id=device_id, captured_at=datetime.now(),
            processing_status=ProcessingStatus.PENDING, created_at=aware, updated_at=aware,
        )


def test_user_repository_round_trip(database_session: Session) -> None:
    user = User(id=uuid4(), created_at=datetime.now(timezone.utc))
    repository = SqlAlchemyUserRepository(database_session)

    repository.add(user)
    database_session.commit()
    database_session.expunge_all()

    stored = repository.get_by_id(user.id)
    assert type(stored) is User
    assert stored == user


def test_device_repository_round_trip(database_session: Session) -> None:
    user = User(id=uuid4(), created_at=datetime.now(timezone.utc))
    SqlAlchemyUserRepository(database_session).add(user)
    database_session.commit()
    device = Device(
        id=uuid4(), user_id=user.id, name="Laptop", created_at=datetime.now(timezone.utc)
    )
    repository = SqlAlchemyDeviceRepository(database_session)

    repository.add(device)
    database_session.commit()
    database_session.expunge_all()

    stored = repository.get_by_id(device.id)
    assert type(stored) is Device
    assert stored == device


@pytest.mark.parametrize(
    "image_reference, status",
    [(None, ProcessingStatus.PENDING), ("captures/example.png", ProcessingStatus.COMPLETED)],
)
def test_capture_repository_round_trip(
    database_session: Session, image_reference: str | None, status: ProcessingStatus
) -> None:
    user = User(id=uuid4(), created_at=datetime.now(timezone.utc))
    device = Device(id=uuid4(), user_id=user.id, name=None, created_at=datetime.now(timezone.utc))
    SqlAlchemyUserRepository(database_session).add(user)
    SqlAlchemyDeviceRepository(database_session).add(device)
    database_session.commit()
    capture = Capture(
        id=uuid4(), device_id=device.id,
        captured_at=datetime(2026, 10, 1, 8, 30, tzinfo=timezone.utc),
        processing_status=status,
        created_at=datetime(2026, 10, 1, 8, 31, tzinfo=timezone.utc),
        updated_at=datetime(2026, 10, 1, 8, 32, tzinfo=timezone.utc),
        image_reference=image_reference,
    )
    repository = SqlAlchemyCaptureRepository(database_session)

    repository.add(capture)
    database_session.commit()
    database_session.expunge_all()

    model = database_session.get(CaptureModel, capture.id)
    assert model is not None
    assert model.image_object_key == image_reference
    assert model.processing_status == status.value
    database_session.expunge_all()

    stored = repository.get_by_id(capture.id)
    assert type(stored) is Capture
    assert stored == capture
    assert stored.processing_status is status


def test_repositories_return_none_for_unknown_ids(database_session: Session) -> None:
    missing_id = uuid4()
    assert SqlAlchemyUserRepository(database_session).get_by_id(missing_id) is None
    assert SqlAlchemyDeviceRepository(database_session).get_by_id(missing_id) is None
    assert SqlAlchemyCaptureRepository(database_session).get_by_id(missing_id) is None


def test_repositories_leave_transaction_control_to_caller(database_session: Session) -> None:
    now = datetime.now(timezone.utc)
    user = User(id=uuid4(), created_at=now)
    device = Device(id=uuid4(), user_id=user.id, name="Laptop", created_at=now)
    capture = Capture(
        id=uuid4(), device_id=device.id, captured_at=now,
        processing_status=ProcessingStatus.PENDING, created_at=now, updated_at=now,
        image_reference="captures/rollback.png",
    )
    user_repository = SqlAlchemyUserRepository(database_session)
    device_repository = SqlAlchemyDeviceRepository(database_session)
    capture_repository = SqlAlchemyCaptureRepository(database_session)

    user_repository.add(user)
    device_repository.add(device)
    capture_repository.add(capture)
    database_session.flush()
    database_session.rollback()

    assert user_repository.get_by_id(user.id) is None
    assert device_repository.get_by_id(device.id) is None
    assert capture_repository.get_by_id(capture.id) is None


def test_capture_worker_state_transitions_are_conditional(database_session: Session) -> None:
    _, device = create_user_and_device(database_session)
    capture = CaptureModel(device_id=device.id, captured_at=datetime.now(timezone.utc))
    database_session.add(capture)
    database_session.commit()
    repository = SqlAlchemyCaptureRepository(database_session)

    assert repository.claim_for_processing(capture.id) is True
    database_session.commit()
    assert repository.claim_for_processing(capture.id) is False
    assert repository.fail_processing(capture.id) is True
    database_session.commit()
    assert repository.complete_processing(capture.id) is False
    assert repository.claim_for_processing(capture.id) is False
    assert repository.get_by_id(capture.id).processing_status is ProcessingStatus.FAILED


def test_worker_service_with_real_repository_commits_before_processing(
    database_session: Session,
) -> None:
    _, device = create_user_and_device(database_session)
    capture = CaptureModel(device_id=device.id, captured_at=datetime.now(timezone.utc))
    database_session.add(capture)
    database_session.commit()
    repository = SqlAlchemyCaptureRepository(database_session)
    observer_engine = create_engine(get_settings().database_url)
    schema = database_session.info["test_schema"]

    class CheckingProcessor:
        calls = 0

        def process(self, capture_id):
            self.calls += 1
            assert capture_id == capture.id
            with observer_engine.connect() as connection:
                connection.execute(text(f"SET search_path TO {schema}, public"))
                state = connection.execute(
                    text("SELECT processing_status FROM captures WHERE id = :id"),
                    {"id": capture_id},
                ).scalar_one()
                assert state == ProcessingStatus.PROCESSING

    processor = CheckingProcessor()
    service = CaptureWorkerService(repository, processor, database_session)
    service.process_capture(capture.id)

    assert processor.calls == 1
    assert repository.get_by_id(capture.id).processing_status is ProcessingStatus.COMPLETED
    observer_engine.dispose()


def test_http_intake_with_real_service_and_repositories(database_session: Session) -> None:
    from fastapi.testclient import TestClient

    from server.api.dependencies import get_image_storage, get_processing_queue, get_session
    from server.main import app

    _, device = create_user_and_device(database_session)
    database_session.commit()

    class FakeStorage:
        stored: list[bytes] = []

        def store(self, image_bytes: bytes) -> str:
            self.stored.append(image_bytes)
            return "captures/integration-image"

        def remove(self, image_reference: str) -> None:
            raise AssertionError("No cleanup expected")

    class FakeQueue:
        enqueued: list = []

        def enqueue_capture_processing(self, capture_id) -> None:
            self.enqueued.append(capture_id)

    storage, queue = FakeStorage(), FakeQueue()
    app.dependency_overrides[get_session] = lambda: database_session
    app.dependency_overrides[get_image_storage] = lambda: storage
    app.dependency_overrides[get_processing_queue] = lambda: queue
    try:
        with TestClient(app) as client:
            response = client.post(
                "/v1/captures",
                data={
                    "device_id": str(device.id),
                    "captured_at": "2026-10-03T01:23:45+07:00",
                },
                files={"image": ("screen.png", b"image bytes", "image/png")},
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 202
    capture_id = UUID(response.json()["id"])
    stored = database_session.get(CaptureModel, capture_id)
    assert stored is not None
    assert stored.processing_status == ProcessingStatus.PENDING
    assert stored.image_object_key == "captures/integration-image"
    assert storage.stored == [b"image bytes"]
    assert queue.enqueued == [capture_id]


def test_http_get_capture_with_real_read_service_and_repository(database_session: Session) -> None:
    from fastapi.testclient import TestClient

    from server.api.dependencies import get_session
    from server.main import app

    _, device = create_user_and_device(database_session)
    captured_at = datetime(2026, 10, 3, 1, 23, 45, tzinfo=timezone.utc)
    capture = CaptureModel(
        device_id=device.id,
        captured_at=captured_at,
        processing_status=ProcessingStatus.PROCESSING,
        image_object_key="private/integration-image",
    )
    database_session.add(capture)
    database_session.commit()

    app.dependency_overrides[get_session] = lambda: database_session
    try:
        with TestClient(app) as client:
            found = client.get(f"/v1/captures/{capture.id}")
            missing = client.get(f"/v1/captures/{uuid4()}")
    finally:
        app.dependency_overrides.clear()

    assert found.status_code == 200
    assert found.json()["id"] == str(capture.id)
    assert found.json()["device_id"] == str(device.id)
    assert found.json()["captured_at"] == "2026-10-03T01:23:45Z"
    assert found.json()["processing_status"] == "processing"
    assert set(found.json()) == {
        "id", "device_id", "captured_at", "processing_status", "created_at", "updated_at"
    }
    assert missing.status_code == 404
    assert missing.json()["error"]["code"] == "capture_not_found"


def test_http_get_image_with_real_repository_and_fake_storage(database_session: Session) -> None:
    from fastapi.testclient import TestClient

    from server.api.dependencies import get_image_storage, get_session
    from server.main import app

    _, device = create_user_and_device(database_session)
    capture = CaptureModel(
        device_id=device.id,
        captured_at=datetime.now(timezone.utc),
        image_object_key="captures/example",
    )
    database_session.add(capture)
    database_session.commit()

    class FakeStorage:
        def __init__(self) -> None:
            self.read_references: list[str] = []

        def read(self, image_reference: str) -> bytes:
            self.read_references.append(image_reference)
            return b"\x00\xffstored screenshot\x80"

    storage = FakeStorage()
    app.dependency_overrides[get_session] = lambda: database_session
    app.dependency_overrides[get_image_storage] = lambda: storage
    try:
        with TestClient(app) as client:
            response = client.get(f"/v1/captures/{capture.id}/image")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/octet-stream"
    assert response.content == b"\x00\xffstored screenshot\x80"
    assert storage.read_references == ["captures/example"]
