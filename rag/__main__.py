"""CLI: ``python -m rag ingest <corpus>`` and ``python -m rag query "<question>"``."""
from __future__ import annotations

import argparse
import sys

from .config import load_config
from .ingest import ingest
from .pipeline import run_pipeline


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="rag", description="Sovereign AI Platform RAG")
    sub = parser.add_subparsers(dest="command", required=True)

    ingest_cmd = sub.add_parser("ingest", help="ingest a corpus directory into Qdrant")
    ingest_cmd.add_argument("corpus", help="path to the corpus directory")

    query_cmd = sub.add_parser("query", help="answer a question against the corpus")
    query_cmd.add_argument("question", help="the question to answer")

    args = parser.parse_args(argv)
    cfg = load_config()

    if args.command == "ingest":
        count = ingest(args.corpus, cfg)
        print(f"ingested {count} chunks into Qdrant collection '{cfg.collection}'")
    elif args.command == "query":
        answer, contexts = run_pipeline(args.question, cfg)
        print(f"ANSWER:\n{answer}\n")
        print(f"CONTEXTS ({len(contexts)}):")
        for i, ctx in enumerate(contexts, start=1):
            preview = ctx.replace("\n", " ")[:200]
            print(f"  [{i}] {preview}...")
    return 0


if __name__ == "__main__":
    sys.exit(main())
