#!/usr/bin/env bash
set -eu

MIGRATIONS_DIR="${MIGRATIONS_DIR:-/migrations}"
ORDER_FILE="${MIGRATIONS_DIR}/migration.order"

echo "Aguardando PostgreSQL em ${PGHOST}:${PGPORT:-5432}..."
until pg_isready -h "${PGHOST}" -p "${PGPORT:-5432}" -U "${PGUSER}" -d "${PGDATABASE}" >/dev/null 2>&1; do
  sleep 1
done

psql -v ON_ERROR_STOP=1 <<'EOSQL'
CREATE TABLE IF NOT EXISTS _migrations_cia (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) UNIQUE NOT NULL,
    executed_at TIMESTAMPTZ DEFAULT NOW()
);
EOSQL

collect_files() {
  if [ -f "${ORDER_FILE}" ]; then
    while IFS= read -r line || [ -n "${line}" ]; do
      line="${line%%#*}"
      line="$(echo "${line}" | tr -d '[:space:]')"
      [ -z "${line}" ] && continue
      echo "${MIGRATIONS_DIR}/${line}"
    done < "${ORDER_FILE}"
  else
    shopt -s nullglob
    for f in "${MIGRATIONS_DIR}"/*.sql; do
      echo "${f}"
    done | sort
  fi
}

mapfile -t files < <(collect_files)

if [ ${#files[@]} -eq 0 ]; then
  echo "Nenhuma migração encontrada em ${MIGRATIONS_DIR}"
  exit 1
fi

for file in "${files[@]}"; do
  if [ ! -f "${file}" ]; then
    echo "ERRO: arquivo não encontrado: ${file}"
    exit 1
  fi
  filename="$(basename "${file}")"
  applied="$(psql -tAc "SELECT 1 FROM _migrations_cia WHERE name = '${filename}' LIMIT 1" || true)"
  if [ "${applied}" = "1" ]; then
    echo "SKIP: ${filename}"
    continue
  fi
  echo "RUN: ${filename}"
  psql -v ON_ERROR_STOP=1 -f "${file}"
  psql -v ON_ERROR_STOP=1 -c "INSERT INTO _migrations_cia (name) VALUES ('${filename}')"
done

echo "Migrações CIA concluídas."
