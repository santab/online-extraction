from __future__ import annotations

import argparse
import json
from pathlib import Path

from extraction_agent.factory import load_and_build
from extraction_agent.graph import PipelineResult, run_pipeline
from extraction_agent.runtime.publisher import publish_resolution


def run_extraction(profile_path: str, file_paths: list[str]) -> PipelineResult:
    loaded = load_and_build(profile_path)
    result = run_pipeline(loaded, file_paths)
    publish_resolution(result.resolution)
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the extraction pipeline for one batch.")
    parser.add_argument("--profile", required=True, help="Path to a profile YAML file.")
    parser.add_argument("--files", nargs="+", required=True, help="Input file paths for this batch.")
    parser.add_argument("--out-dir", default=".", help="Where to write structured_output.json and resolution.json.")
    args = parser.parse_args()

    result = run_extraction(args.profile, args.files)

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "structured_output.json").write_text(json.dumps(result.structured_output, indent=2, default=str))
    (out_dir / "resolution.json").write_text(json.dumps(result.resolution, indent=2, default=str))


if __name__ == "__main__":
    main()
