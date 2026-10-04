import argparse
import sys
from pathlib import Path
from typing import NoReturn

import yaml
from pydantic import ValidationError

from mreg.evidence.normalize import read_json
from mreg.evidence.validate import InputError, validate_evidence
from mreg.gate.evaluator import evaluate
from mreg.models.result import Result
from mreg.policy.loader import read_policy
from mreg.policy.validate import validate_policy
from mreg.reporting.json_report import replay, write_review


class Parser(argparse.ArgumentParser):
    def error(self, message: str) -> NoReturn:
        self.print_usage(sys.stderr)
        self.exit(3, f"mreg: {message}\n")


def main(argv: list[str] | None = None) -> int:
    parser = Parser(description="Deterministic model release evidence gate")
    parser.add_argument("--version", action="version", version="mreg 0.1.0")
    commands = parser.add_subparsers(dest="command", required=True, parser_class=Parser)
    check = commands.add_parser("check")
    check.add_argument("--evidence", type=Path, required=True)
    check.add_argument("--policy", type=Path, required=True)
    check.add_argument("--output", type=Path, required=True)
    replay_parser = commands.add_parser("replay")
    replay_parser.add_argument("--bundle", type=Path, required=True)
    replay_parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    evidence = policy = None
    try:
        if args.command == "check":
            try:
                policy = validate_policy(read_policy(args.policy))
            except (ValueError, yaml.YAMLError) as error:
                if isinstance(error, InputError):
                    raise
                raise InputError("INVALID_POLICY") from error
            try:
                evidence = validate_evidence(read_json(args.evidence))
            except ValueError as error:
                if isinstance(error, InputError):
                    raise
                raise InputError("INVALID_EVIDENCE") from error
            result = evaluate(evidence, policy)
        else:
            result, evidence, policy = replay(read_json(args.bundle))
    except InputError as error:
        result = Result(verdict="ERROR", reason_codes=[error.code])
    except (OSError, ValueError, TypeError, RecursionError, ValidationError):
        # Never echo input contents or raw exception strings (they may contain secrets).
        result = Result(verdict="ERROR", reason_codes=["EXECUTION_ERROR"])
    try:
        write_review(args.output, result, evidence, policy)
    except (OSError, ValueError):
        print("ERROR: unable to write review artifacts", file=sys.stderr)
        return 3
    print(f"{result.verdict}: {', '.join(result.reason_codes) or 'CHECK_PASSED'}")
    return result.exit_code
