-- Script exécuté automatiquement par l'image PostgreSQL au PREMIER démarrage
-- (quand le volume de données est vide). Il recrée les tables faites dans DBeaver.

CREATE TABLE IF NOT EXISTS users (
    id              SERIAL PRIMARY KEY,
    username        VARCHAR(50)  NOT NULL UNIQUE,
    hashed_password VARCHAR(255) NOT NULL
);

CREATE TABLE IF NOT EXISTS user_books (
    id      SERIAL PRIMARY KEY,
    -- Pas de clé étrangère vers users : en microservices, le service books ne
    -- dépend pas des tables du service auth. Il fait confiance au jeton JWT.
    user_id INTEGER      NOT NULL,
    title   VARCHAR(255) NOT NULL,
    author  VARCHAR(255),
    status  VARCHAR(20)  NOT NULL DEFAULT 'à lire'
);

CREATE INDEX IF NOT EXISTS idx_user_books_user_id ON user_books(user_id);
