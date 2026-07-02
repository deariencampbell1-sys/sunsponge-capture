"""`capturd walk` CLI — thin wrapper over the same coordinator the MCP surface uses.

Subcommands: record / stop / status / list / export / edit / delete.
Both the human CLI and the agent MCP surface land on the same code path
(``capturd.walk.coordinator.DemoForge``) — no duplicate business logic.

W1 (recorder-as-agent-entrypoint), W2 (zoom pipeline), W3 (voice-sync), W4
(expanded MCP surface) will fill in the actual implementations. This file
is the argparse skeleton the workers hang their work on.
"""

from __future__ import annotations

import argparse
import json
import sys


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="capturd walk",
        description="Agent-made interactive product walkthroughs.",
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("record", help="Start a walkthrough recording session")
    p.add_argument("--url", required=True, help="URL to walk")
    p.add_argument("--name", required=True, help="Demo name")
    p.add_argument("--goal", required=True, help="What the flow demonstrates")
    p.add_argument("--agent", action="store_true",
                   help="Agent-driven (LLM picks each next click). Default: headful, human clicks.")
    p.add_argument("--viewport", default="1440x900", help="Recording viewport (WxH)")

    p = sub.add_parser("stop", help="Stop a recording and kick off AI enrichment")
    p.add_argument("--session-id", required=True)

    p = sub.add_parser("status", help="Check enrichment progress for a demo")
    p.add_argument("--demo-id", required=True)

    p = sub.add_parser("list", help="List recorded demos")
    p.add_argument("--json", action="store_true", help="Machine-readable output")

    p = sub.add_parser("export", help="Render a demo as viewer HTML / MP4 / GIF")
    p.add_argument("--demo-id", required=True)
    p.add_argument("--format", choices=["html", "mp4", "gif"], default="html")
    p.add_argument("--out", help="Output path (default: alongside the demo JSON)")

    p = sub.add_parser("edit", help="Edit a step's annotation / voiceover / camera")
    p.add_argument("--demo-id", required=True)
    p.add_argument("--step", type=int, required=True)
    p.add_argument("--annotation", help="Rewrite the annotation")
    p.add_argument("--regenerate-voice", action="store_true")

    p = sub.add_parser("delete", help="Delete a demo and its files")
    p.add_argument("--demo-id", required=True)

    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    # Spine stub: workers W1-W4 replace this with real dispatch to the coordinator.
    # We keep the argparse contract stable so their diff stays small.
    sys.stderr.write(
        f"[spine-stub] `capturd walk {args.cmd}` — implementation lands in W1-W4.\n"
    )
    sys.stdout.write(json.dumps(vars(args), indent=2) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
