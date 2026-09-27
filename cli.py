"""
cli.py
------
Command-line entry point. Run extraction on a resume, optionally compare
it against a job description.

Usage:
    python cli.py sample_data/sample_resume.txt
    python cli.py sample_data/sample_resume.txt --jd sample_data/sample_job_description.txt
"""

import argparse
import json
import sys

from extractor import extract, compare_to_jd


def read_file(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def print_result(result_dict: dict, title: str):
    print(f"\n{'=' * 60}\n{title}\n{'=' * 60}")
    print(json.dumps(result_dict, indent=2))


def main():
    parser = argparse.ArgumentParser(description="Extract structured info from a resume.")
    parser.add_argument("resume_path", help="Path to a .txt resume file")
    parser.add_argument("--jd", help="Path to a .txt job description file to compare against", default=None)
    args = parser.parse_args()

    resume_text = read_file(args.resume_path)
    result = extract(resume_text)
    print_result(result.to_dict(), "EXTRACTED RESUME DATA")

    if args.jd:
        jd_text = read_file(args.jd)
        comparison = compare_to_jd(resume_text, jd_text)
        print_result(comparison, "RESUME vs JOB DESCRIPTION MATCH")
        print(f"\nMatch score: {comparison['match_percentage']}%\n")


if __name__ == "__main__":
    sys.exit(main())
