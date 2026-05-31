import argparse
import ast
import asyncio
import json
import sys
from pathlib import Path
from typing import Any

import asyncpg

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.core.config import settings

QUESTIONS_DIR = ROOT / "docs" / "json_questoes"

METRICS = [
    ("Taxa de compreensao", "CompreensaoTextual"),
    ("Clareza da resposta", "ClarezaResposta"),
    ("Teste do embed", "TesteDoEmbed"),
    ("Direito Administrativo", "DireitoAdministrativo"),
    ("Matematica", "Matematica"),
    ("Raciocinio Logico", "RaciocinioLogico"),
    ("Vibe Coding", "VibeCoding"),
]


def load_json(name: str) -> Any:
    with open(QUESTIONS_DIR / name, "r", encoding="utf-8") as file:
        return json.load(file)


def read_text(relative_path: str) -> str:
    with open(QUESTIONS_DIR / relative_path, "r", encoding="utf-8") as file:
        return file.read()


def extract_python_constant(source: str, name: str) -> str:
    tree = ast.parse(source)
    for node in tree.body:
        if isinstance(node, ast.Assign):
            targets = [target.id for target in node.targets if isinstance(target, ast.Name)]
            if name in targets and isinstance(node.value, ast.Constant):
                if isinstance(node.value.value, str):
                    return node.value.value
    raise ValueError(f"Constante Python nao encontrada: {name}")


async def ensure_metrics(conn: asyncpg.Connection) -> dict[str, str]:
    metric_ids: dict[str, str] = {}
    for label, metric_type in METRICS:
        metric_id = await conn.fetchval(
            """
            INSERT INTO metricas (metricas, tipo)
            VALUES ($1, $2::benchmark_tipo_metrica)
            ON CONFLICT (tipo) DO UPDATE
            SET metricas = EXCLUDED.metricas
            RETURNING id
            """,
            label,
            metric_type,
        )
        metric_ids[metric_type] = str(metric_id)
    return metric_ids


async def insert_question(
    conn: asyncpg.Connection,
    metric_id: str,
    pergunta: dict[str, Any],
    gabarito: dict[str, Any],
) -> bool:
    row = await conn.fetchrow(
        """
        INSERT INTO banco_questoes (metrica_id, pergunta, gabarito)
        SELECT $1::uuid, $2::jsonb, $3::jsonb
        WHERE NOT EXISTS (
            SELECT 1
            FROM banco_questoes
            WHERE metrica_id = $1::uuid
              AND pergunta = $2::jsonb
              AND gabarito = $3::jsonb
        )
        RETURNING id
        """,
        metric_id,
        json.dumps(pergunta, ensure_ascii=False),
        json.dumps(gabarito, ensure_ascii=False),
    )
    return row is not None


async def seed_questions(conn: asyncpg.Connection, metric_ids: dict[str, str]) -> int:
    inserted = 0

    inserted += await insert_question(
        conn,
        metric_ids["CompreensaoTextual"],
        {
            "categoria": "Meio Ambiente",
            "premissa": "Plantar arvores melhora a qualidade do ar.",
            "hipotese": "A arborizacao contribui para um ambiente mais saudavel.",
            "nivel": "Facil",
        },
        {"resposta": "Implicacao"},
    )

    for item in load_json("compreensao-textual.json")[:10]:
        inserted += await insert_question(
            conn,
            metric_ids["CompreensaoTextual"],
            {
                "categoria": item["categoria"],
                "premissa": item["premissa"],
                "hipotese": item["hipotese"],
                "nivel": item["hipotese"],
            },
            {"resposta": item["gabarito"]},
        )

    for item in load_json("clareza-resposta.json")[:10]:
        inserted += await insert_question(
            conn,
            metric_ids["ClarezaResposta"],
            {"texto": item["texto"], "gabarito": item["gabarito"]},
            {"resposta": item["gabarito"]},
        )

    cartas_servico = load_json("cartas-servico.json")
    for item in cartas_servico["perguntas"][:10]:
        inserted += await insert_question(
            conn,
            metric_ids["TesteDoEmbed"],
            {"pergunta": item["pergunta"]},
            {},
        )

    for item in load_json("direito-administrativo.json")[:10]:
        inserted += await insert_question(
            conn,
            metric_ids["DireitoAdministrativo"],
            {"pergunta": item["pergunta"], "nivel": item["nivel"]},
            {"gabarito": item["gabarito"], "justificativa": item["justificativa"]},
        )

    for item in load_json("matematica.json")[:10]:
        inserted += await insert_question(
            conn,
            metric_ids["Matematica"],
            {
                "pergunta": item["problem"],
                "nivel": item["level"],
                "tipo": item["type"],
            },
            {"gabarito": item["solution"]},
        )

    for item in load_json("raciocinio-logico.json")[:10]:
        inserted += await insert_question(
            conn,
            metric_ids["RaciocinioLogico"],
            {"pergunta": item["pergunta"], "nivel": item["level"]},
            {"gabarito": item["Gabarito"]},
        )

    for item in load_json("vibe-coding.json"):
        source = read_text(item["base_script_path"])
        base_script = extract_python_constant(source, "sum_two_base")
        context = extract_python_constant(source, "sum_two_context")
        gabarito = extract_python_constant(source, "sum_two_gabarito")
        problema = read_text(item["problema_path"])
        inserted += await insert_question(
            conn,
            metric_ids["VibeCoding"],
            {
                "problema": problema,
                "contexto": context,
                "baseScript": base_script,
                "nivel": item["nivel"],
                "tipo": item["tipo"],
            },
            {"gabarito": gabarito},
        )

    return inserted


async def seed_cartas_servico(conn: asyncpg.Connection) -> int:
    data = load_json("cartas-servico.json")
    inserted = 0
    sections = [
        ("oque", "O que e o servico"),
        ("quem", "Para quem e o servico"),
        ("como", "Como utilizar o servico"),
    ]

    for index, item in enumerate(data["cartas"]):
        for field, title_prefix in sections:
            content = item.get(field)
            if not content:
                continue
            result = await conn.execute(
                """
                INSERT INTO cartas_servico (id, content, metadata, embedding)
                VALUES ($1, $2, $3::jsonb, NULL)
                ON CONFLICT (id) DO UPDATE
                SET content = EXCLUDED.content,
                    metadata = EXCLUDED.metadata
                """,
                f"cartas-{field}-{index}",
                content,
                json.dumps(
                    {
                        "title": (
                            f'{title_prefix} "{item.get("nome", "")}" '
                            f'do orgao "{item.get("orgao", "")}"'
                        )
                    },
                    ensure_ascii=False,
                ),
            )
            if result == "INSERT 0 1":
                inserted += 1

    return inserted


async def main(skip_cartas: bool) -> None:
    conn = await asyncpg.connect(settings.DATABASE_URL)
    try:
        async with conn.transaction():
            metric_ids = await ensure_metrics(conn)
            question_count = await seed_questions(conn, metric_ids)
            cartas_count = 0 if skip_cartas else await seed_cartas_servico(conn)
    finally:
        await conn.close()

    print(
        json.dumps(
            {
                "metricas": len(METRICS),
                "questoes_inseridas": question_count,
                "cartas_servico_inseridas": cartas_count,
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Seed de benchmarking equivalente ao seed Prisma original."
    )
    parser.add_argument(
        "--skip-cartas",
        action="store_true",
        help="Nao inserir cartas_servico.",
    )
    args = parser.parse_args()
    asyncio.run(main(skip_cartas=args.skip_cartas))
