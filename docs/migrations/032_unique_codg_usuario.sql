-- Migration to enforce uniqueness on codg_usuario column in users table
ALTER TABLE users ADD CONSTRAINT uq_users_codg_usuario UNIQUE (codg_usuario);
