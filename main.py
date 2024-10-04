from sqlmodel import Session, create_engine, select
from dotenv import load_dotenv
from app.models import Video
import os

if __name__ == "__main__":
    load_dotenv()

    engine = create_engine(
        f"postgresql://{os.getenv('POSTGRES_USER')}:{os.getenv('POSTGRES_PASSWORD')}@localhost/{os.getenv('POSTGRES_DB')}"
    )

    # Sample for db
    with Session(engine) as session:
        statement = select(Video)
        results = session.exec(statement)
        for acc in results:
            print(acc)
