"""
SAT Assignment Part 2 - Non-consecutive Sudoku Solver (puzzle -> SAT/UNSAT)

Do NOT modify this file - instead, implement your function in encoder.py

Usage:
  python main.py --in <puzzle.txt>

Behavior:
  - Reads a Sudoku puzzle in plain text format (N x N grid, 0 = empty).
  - Encodes it to CNF, runs the solver, and decides satisfiability.
  - Prints exactly one line to stdout:
        SAT
     or
        UNSAT
"""

import argparse
from typing import Tuple, Iterable
from encoder import to_cnf
from encoder import read_dimacs
from solver_random import solve_cnf_random
from solver import solve_cnf_dlcs
from solver_jw import solve_cnf_jw
from solver_mom import solve_cnf_mom
import os
import pathlib
import re


def get_case_id(path: str) -> int:
    CASE_RE = re.compile(r".*uf\d+-0(\d+)\.cnf$", re.IGNORECASE)
    m = CASE_RE.search(path)
    if not m:
        return float("inf")
    return int(m.group(1))


def parse_args():
    import argparse

    p = argparse.ArgumentParser()
    p.add_argument("--in", dest="inp", required=True, help="Input file path")
    p.add_argument(
        "--cnf", dest="cnf", action="store_true", help="Treat input as DIMACS CNF"
    )
    p.add_argument(
        "--out",
        dest="out",
        type=str,
        default="out.txt",
        help="Output path",
    )
    return p.parse_args()


def main():
    args = parse_args()
    # Output file
    output_file = pathlib.Path(args.out)
    # Clear file content
    output_file.write_text("")
    # Build list of files to process
    input_paths = []

    if os.path.isdir(args.inp):
        # Folder: run all .cnf files if --cnf was given
        for name in os.listdir(args.inp):
            full = os.path.join(args.inp, name)
            if not os.path.isfile(full):
                continue
            if args.cnf and not name.lower().endswith(".cnf"):
                continue
            input_paths.append(full)
    else:
        # Single file
        input_paths.append(args.inp)

    input_paths.sort(key=get_case_id)
    # Run each file
    for path in input_paths:
        string = path + "\n"

        if args.cnf:
            clauses, num_vars = read_dimacs(path)
        else:
            clauses, num_vars = to_cnf(path)

        # ---- RANDOM ----
        status, _, stats = solve_cnf_random(clauses, num_vars)
        string += status + "\n" + stats + "\n"

        # ---- DLCS ----
        status, _, stats = solve_cnf_dlcs(clauses, num_vars)
        string += status + "\n" + stats + "\n"

        # ---- JW ----
        status, _, stats = solve_cnf_jw(clauses, num_vars)
        string += status + "\n" + stats + "\n"

        # ---- MOM ----
        status, _, stats = solve_cnf_mom(clauses, num_vars)
        string += status + "\n" + stats + "\n"

        # Optional separator
        string += "-" * 40 + "\n"

        # Write to output file and std out
        print(string)
        with output_file.open("a") as f:
            f.write(string)


def parse_dimacs(input_path: str) -> Tuple[Iterable[Iterable[int]], int]:
    close = False
    if isinstance(input_path, str):
        file = open(input_path, "r")
        close = True
    else:
        file = input_path

    line = file.readline()

    components = line.strip().split(" ")

    if len(components) != 4 or components[0] != "p" or components[1] != "cnf":
        print(
            "Wrong file format! Expected first line to be 'p cnf NUM_VARS NUM_CLAUSES"
        )
        exit(1)

    num_vars = int(components[2])
    num_clauses = int(components[3])

    clauses = []

    line = file.readline()
    while line:
        numbers = [int(x) for x in line.strip().split(" ")]

        if numbers[-1] != 0:
            print("Wrong format! Clause lines must be terminated with a 0")

        clauses.append(numbers[:-1])

        line = file.readline()

    return clauses, num_vars


if __name__ == "__main__":
    main()


# what to run in terminal: python3 main.py --in <instance folder> --cnf --out <output file name>.txt
