"""SQL Academy 1.4 store adapter module."""


from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Iterable, List, Optional, Tuple

import sqlalchemy as sa
import sqlalchemy.orm as orm
import sqlalchemy_utils as sa_utils
from code_wake.config import Config
from code_wake.stack_trace import Stacktrace

from . import utils


class Sql14Store:
    """SQL Academy 1.4 store adapter."""

    Base = orm.declarative_base()  # type: Any

    class Environment(Base):
        __tablename__ = "environments"

        id = sa.Column(sa.Integer, primary_key=True)
        name = sa.Column(sa.String, unique=True, nullable=False)

        def __repr__(self):
            return f"<Sql14Store.Environment(id='{self.id}')>"

    class Process(Base):
        __tablename__ = "processes"

        id = sa.Column(sa.Integer, primary_key=True)
        run_ts = sa.Column(sa.Float, nullable=False, default=lambda: datetime.now().timestamp())
        environment_id = sa.Column(sa.Integer, sa.ForeignKey("environments.id"), nullable=True)
        pid = sa.Column(sa.Integer)
        username = sa.Column(sa.String)
        fqdn = sa.Column(sa.String)
        exe_path = sa.Column(sa.String)
        app_id = sa.Column(sa.Integer, sa.ForeignKey("apps.id"), nullable=False)
        app_vsn_id = sa.Column(sa.Integer, sa.ForeignKey("app_vsns.id"), nullable=True)
        environment = orm.relationship("Environment", lazy="joined")
        app = orm.relationship("App", lazy="joined")
        app_vsn = orm.relationship("AppVsn", lazy="joined")

        run_ts_index = sa.Index("run_ts")
        app_vsn_env_index = sa.Index("app_id", "app_vsn_id", "environment_id")

        def __repr__(self):
            return f"<Sql14Store.Process(id='{self.id}')>"

    class App(Base):
        __tablename__ = "apps"

        id = sa.Column(sa.Integer, primary_key=True)
        name = sa.Column(sa.String, unique=True, nullable=False)
        vsns = orm.relationship("AppVsn", lazy="joined", back_populates="app")

        def __repr__(self):
            return f"<Sql14Store.App(id='{self.id}')>"

    class AppVsn(Base):
        __tablename__ = "app_vsns"

        id = sa.Column(sa.Integer, primary_key=True)
        vsn = sa.Column(sa.String, nullable=False)
        app_id = sa.Column(sa.Integer, sa.ForeignKey("apps.id"), nullable=False)
        app = orm.relationship("App", lazy="joined")
        app = orm.relationship("App", lazy="joined", back_populates="vsns")

        vsn_app_unique = sa.UniqueConstraint('vsn", "app_id')

        def __repr__(self):
            return f"<Sql14Store.AppVsn(id='{self.id}')>"

    class Event(Base):
        __tablename__ = "events"

        id = sa.Column(sa.Integer, primary_key=True)
        when_ts = sa.Column(sa.Float, nullable=False, default=lambda: datetime.now().timestamp())
        process_id = sa.Column(sa.Integer, sa.ForeignKey("processes.id"), nullable=False)
        digest = sa.Column(sa.BINARY, nullable=True)
        stacktrace_id = sa.Column(sa.Integer, sa.ForeignKey("stacktraces.id"), nullable=True)
        process = orm.relationship("Process", lazy="joined")
        data = orm.relationship("EventData", back_populates="event", lazy="joined")
        stacktrace = orm.relationship("Stacktrace", lazy="joined")

        when_ts_index = sa.Index("when_ts")

        def __repr__(self):
            return f"<Sql14Store.Event(id='{self.id}')>"

    class EventData(Base):
        __tablename__ = "events_data"

        id = sa.Column(sa.Integer, primary_key=True)
        key = sa.Column(sa.String, nullable=False)
        val = sa.Column(sa.String, nullable=True)
        event_id = sa.Column(sa.Integer, sa.ForeignKey("events.id"), nullable=False)
        event = orm.relationship("Event", lazy="joined")

        keyvals_index = sa.Index("key", "val")

        def __repr__(self):
            return f"<Sql14Store.EventData(id='{self.id}')>"

    class Stacktrace(Base):
        __tablename__ = "stacktraces"

        id = sa.Column(sa.Integer, primary_key=True)
        digest = sa.Column(sa.BINARY, nullable=False, unique=True)
        stackframes = orm.relationship(
            "Stackframe",
            back_populates="stacktrace",
            lazy="joined",
            order_by="-Stackframe.id",
        )

        def __repr__(self):
            return f"<Sql14Store.Stacktrace(id='{self.id}')>"

    class Stackframe(Base):
        __tablename__ = "stackframes"

        id = sa.Column(sa.Integer, primary_key=True)
        stacktrace_id = sa.Column(sa.Integer, sa.ForeignKey("stacktraces.id"), nullable=False)
        filename = sa.Column(sa.String, unique=False, nullable=False)
        lineno = sa.Column(sa.Integer, unique=False, nullable=False)
        src = sa.Column(sa.String, unique=False)
        stacktrace = orm.relationship("Stacktrace", lazy="joined")

        def __repr__(self):
            return f"<Sql14Store.Stacktrace(id='{self.id}')>"

    def __init__(self, dsn: str, *args, **kwargs):
        self._engine = self._create_engine(dsn, *args, **kwargs)
        self._session_factory = self._create_session_factory(self._engine, *args, **kwargs)

        self._setup_tables()

    def _create_engine(self, dsn, *args, echo=False, **kwargs) -> sa.engine.base.Engine:
        return sa.create_engine(dsn, echo=echo)

    def _create_session_factory(self, engine: sa.engine.base.Engine, *args, **kwargs) -> orm.session.sessionmaker:
        return orm.sessionmaker(bind=engine)

    @property
    def session(self):
        return self._session_factory

    def _setup_tables(self):
        Sql14Store.Base.metadata.create_all(self._engine)

    def insert_app(self, name: str, vsn: Optional[str] = None) -> Sql14Store.App:
        with self.session() as session:
            App = self.App
            app_record = App(name=name)
            session.add(app_record)
            session.flush()
            session.refresh(app_record)

            if vsn is not None:
                AppVsn = self.AppVsn
                app_vsn_record = AppVsn(vsn=vsn, app_id=app_record.id)
                session.add(app_vsn_record)
                session.flush()
                session.refresh(app_vsn_record)

            session.flush()

            return app_record

    def insert_app_vsn(self, app_id: int, vsn: str) -> Sql14Store.AppVsn:
        with self.session() as session:
            app_vsn_record = self.AppVsn(vsn=vsn, app_id=app_id)
            session.add(app_vsn_record)
            session.flush()
            session.refresh(app_vsn_record)

            return app_vsn_record

    def get_environment_by_id(self, id: int) -> Optional[Sql14Store.Environment]:
        with self.session() as session:
            return self._get_environment_by_id(session, id)

    def _get_environment_by_id(self, session, id: int) -> Optional[Sql14Store.Environment]:
        return session.query(self.Environment).get(id)

    def get_environment_by_name(self, name: str) -> Optional[Sql14Store.Environment]:
        with self.session() as session:
            return self._get_environment_by_name(session, name)

    def _get_environment_by_name(self, session, name: str) -> Optional[Sql14Store.Environment]:
        env_records = session.query(self.Environment).filter(self.Environment.name == name).all()
        return None if len(env_records) == 0 else env_records[0]

    def get_app_by_id(self, id: int) -> Optional[Sql14Store.App]:
        with self.session() as session:
            return self._get_app_by_id(session, id)

    def _get_app_by_id(self, session, id: int) -> Optional[Sql14Store.App]:
        return session.query(self.App).get(id)

    def get_app_by_name(self, name: str) -> Optional[Sql14Store.App]:
        with self.session() as session:
            return self._get_app_by_name(session, name)

    def _get_app_by_name(self, session, name: str) -> Optional[Sql14Store.App]:
        app_records = session.query(self.App).filter(self.App.name == name).all()
        return None if len(app_records) == 0 else app_records[0]

    def get_app_vsn_by_id(self, id: int) -> Optional[Sql14Store.AppVsn]:
        with self.session() as session:
            app_vsn_record = self._get_app_vsn_by_id(session, id)
            session.refresh(app_vsn_record)
            return app_vsn_record

    def _get_app_vsn_by_id(self, session, id: int) -> Optional[Sql14Store.AppVsn]:
        return session.query(self.AppVsn).get(id)

    def get_process_by_id(self, id: int) -> Optional[Sql14Store.Process]:
        with self.session() as session:
            return self._get_process_by_id(session, id)

    def _get_process_by_id(self, session, id: int) -> Optional[Sql14Store.Process]:
        process_record = session.query(self.Process).get(id)

        if process_record is not None:
            app_record = session.query(self.App).get(process_record.app_id)
            app_vsn = None
            if process_record.app_vsn_id is not None:
                app_vsn_record = session.query(self.AppVsn).get(process_record.app_vsn_id)
                app_vsn = app_vsn_record.vsn
            env_name = None
            if process_record.environment_id is not None:
                env_record = session.query(self.Environment).get(process_record.environment_id)
                env_name = env_record.name

        return process_record

    def insert_process(self, unstored_process: Process) -> Sql14Store.Process:
        with self.session() as session:
            env_record = None
            environment_id = None

            if unstored_process.environment is not None:
                env_record = self._get_environment_by_name(session, unstored_process.environment.name)

                if env_record is None:
                    env_record = self.Environment(name=unstored_process.environment.name)
                    session.add(env_record)
                    session.flush()
                    session.refresh(env_record)

                environment_id = env_record.id

            app_record = self._get_app_by_name(session, unstored_process.app.name)

            if app_record is None:
                app_record = self.App(name=unstored_process.app.name)
                session.add(app_record)

            app_vsn_id = None

            if unstored_process.app_vsn is not None:
                app_vsn_records = (
                    session.query(self.AppVsn).filter(self.AppVsn.vsn == unstored_process.app_vsn.vsn).all()
                )

                if len(app_vsn_records) == 0:
                    app_vsn_record = self.AppVsn(vsn=unstored_process.app_vsn.vsn, app_id=app_record.id)
                    session.add(app_vsn_record)
                    session.flush()
                    session.refresh(app_vsn_record)
                    app_vsn_id = app_vsn_record.id
                else:
                    app_vsn_record = app_vsn_records[0]
                    app_vsn_id = app_vsn_record.id

            session.flush()

            process_record = self.Process(
                environment_id=environment_id,
                app_id=app_record.id,
                app_vsn_id=app_vsn_id,
                pid=unstored_process.pid,
                username=unstored_process.username,
                fqdn=unstored_process.fqdn,
                exe_path=unstored_process.exe_path,
            )
            session.add(process_record)
            session.commit()
            session.refresh(process_record)

            return process_record

    def insert_event(
        self,
        process: Process,
        data: Optional[Iterable[Tuple[str, str]]] = None,
        exc: Optional[Exception] = None,
        inc_st: Optional[bool] = None,
        st_len: Optional[int] = None,
        st_data: Optional[List[str, int, str]] = None,
        when_ts: float = None,
        sync: bool = False,
    ) -> Optional[Sql14Store.Event]:
        with self.session() as session:
            if inc_st is None:
                inc_st = Config()["stacktraces"]["include"]["for_non_exceptions" if exc is None else "from_exceptions"]

            st = None

            if inc_st:
                if st_data is not None:
                    st = Stacktrace.from_data(st_data, st_len=st_len)
                elif exc is not None:
                    st = Stacktrace.from_exc(exc, st_len=st_len)
                else:
                    st = Stacktrace.from_caller(st_len=st_len)

            stacktrace_id = None

            if st is not None:
                digest = st.digest()

                stacktrace_records = session.query(self.Stacktrace).filter(self.Stacktrace.digest == digest).all()
                if len(stacktrace_records) == 0:
                    stacktrace_record = self.Stacktrace(digest=digest)
                    session.add(stacktrace_record)
                    session.flush()

                    for sf in st.stackframes:
                        stackframe_record = self.Stackframe(
                            stacktrace_id=stacktrace_record.id,
                            filename=sf.filename,
                            lineno=sf.lineno,
                            src=sf.src,
                        )
                        session.add(stackframe_record)
                else:
                    stacktrace_record = stacktrace_records[0]
                    session.add(stacktrace_record)

                stacktrace_id = stacktrace_record.id

            event_record = self.Event(
                process_id=process.id,
                digest=None if data is None else utils.data_digest(data),
                stacktrace_id=stacktrace_id,
                when_ts=when_ts,
            )
            session.add(event_record)

            session.flush()

            if data is not None:
                for key, val in data:
                    eventdata_record = self.EventData(event_id=event_record.id, key=key, val=val)
                    session.add(eventdata_record)

            session.commit()
            session.refresh(event_record)

            return event_record if sync else None

    def get_events_by_data(
        self, where: Iterable[Tuple[str, str]], process_id: Optional[int] = None
    ) -> List[Sql14Store.Event]:
        with self.session() as session:
            query = session.query(self.Event)

            if process_id is not None:
                query = query.filter(self.Event.process_id == process_id)

            for key, val in where:
                EventDataAlias = orm.aliased(self.EventData)
                query = query.join(EventDataAlias).filter(EventDataAlias.key == key).filter(EventDataAlias.val == val)

            event_records = query.all()
            session.flush()

            return event_records
