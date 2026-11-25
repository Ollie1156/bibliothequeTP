import os

from dotenv import load_dotenv
from sqlalchemy import URL, create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

# En local, lit le fichier .env (ignoré par Git). En conteneur, les variables
# sont injectées par Docker Compose ou par Kubernetes (ConfigMap + Secret).
load_dotenv()


def build_database_url():
    # 1) Compatibilité avec le lancement local : une URL complète dans .env
    if os.getenv("DATABASE_URL"):
        return os.getenv("DATABASE_URL")

    # 2) En conteneur : l'URL est reconstruite à partir de variables séparées.
    #    Host/port/nom de base viennent de la ConfigMap (non sensible),
    #    utilisateur/mot de passe viennent du Secret.
    return URL.create(
        drivername="postgresql+pg8000",
        username=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        host=os.getenv("DB_HOST", "localhost"),
        port=int(os.getenv("DB_PORT", "5432")),
        database=os.getenv("DB_NAME", "bibliotheque"),
    )


# pool_pre_ping : vérifie la connexion avant de l'utiliser (utile si la base redémarre)
engine = create_engine(build_database_url(), pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
