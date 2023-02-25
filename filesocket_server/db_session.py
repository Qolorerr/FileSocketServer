from pathlib import Path
import sqlalchemy as sa
import sqlalchemy.orm as orm
from sqlalchemy.orm import Session
import sqlalchemy.ext.declarative as dec


SqlAlchemyBase = dec.declarative_base()
__factory = None


def global_init(db_file: Path):
    global __factory
    if __factory:
        return
    if not db_file.exists():
        raise Exception("You need to set db file name")
    conn_str = f'sqlite:///{db_file}?check_same_thread=False'
    print(f"Connection to base {db_file}\n")
    engine = sa.create_engine(conn_str, echo=False)
    __factory = orm.sessionmaker(bind=engine)
    import filesocket_server.__all_models
    SqlAlchemyBase.metadata.create_all(engine)


def create_session() -> Session:
    global __factory
    return __factory()
