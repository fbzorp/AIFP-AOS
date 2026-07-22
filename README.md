# AIFP-AOS

## Setup
pip install -e .

alembic -c alembic.ini upgrade head

Note: Do not `import alembic.env` directly; use Alembic CLI.