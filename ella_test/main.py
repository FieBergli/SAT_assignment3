#!/usr/bin/env python3
"""
SAT Assignment Part 2 - Non-consecutive Sudoku Solver (puzzle -> SAT/UNSAT)

Do NOT modify this file - instead, implement your function in encoder.py

Usage:
  Single file:
    python main.py --in <puzzle.txt>
    python main.py --in uf50-218/uf50-01.cnf --cnf

  Batch over directory of CNF files:
    python main.py --in uf50-218 --cnf --out results_uf50-218.txt
    python main.py --in uf50-218 --cnf --limit 100 --out results_100.txt

Behavior:
  - Reads a Sudoku puzzle in plain text format (N x N grid, 0 = empty),
    OR a DIMACS CNF file (if --cnf is passed).
  - Encodes it to CNF (for Sudoku), runs the solver(s), and decides satisfiability.
  - For batch mode (directory), runs .cnf files (or all files for Sudoku)
    and logs results to stdout and/or the output file if --out is specified.
"""
import sys, os
# add parent folder to the Python module search path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
import argparse
from typing import Tuple, Iterable
from encoder import to_cnf
from encoder import read_dimacs
from solver_random import solve_cnf_random
from solver import solve_cnf_dlcs
from solver_jw import solve_cnf_jw
from solver_mom import solve_cnf_mom


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--in", dest="inp", required=True, help="Input file path OR directory")
    p.add_argument("--cnf", dest="cnf", action="store_true", help="Treat input as DIMACS CNF")
    p.add_argument("--out", dest="out", help="Output results file (for logging)")
    p.add_argument("--limit", dest="limit", type=int, help="Limit number of instances to process")
    return p.parse_args()


def run_on_instance(path: str, is_cnf: bool):
    """
    Run all solvers on a single instance (file), return statuses as a dict.
    """
    if is_cnf:
        clauses, num_vars = read_dimacs(path)
    else:
        clauses, num_vars = to_cnf(path)

    status_rand, _ = solve_cnf_random(clauses, num_vars)
    status_dlcs, _ = solve_cnf_dlcs(clauses, num_vars)
    status_jw, _ = solve_cnf_jw(clauses, num_vars)
    status_mom, _ = solve_cnf_mom(clauses, num_vars)

    return {
        "random": status_rand,
        "dlcs": status_dlcs,
        "jw": status_jw,
        "mom": status_mom,
    }


def main():
    args = parse_args()

    inp_path = args.inp
    is_dir = os.path.isdir(inp_path)

    # Open output file if given; otherwise we'll just use stdout.
    out_file = None
    if args.out is not None:
        out_file = open(args.out, "w")

    def write(line: str):
        # Always print to terminal
        print(line)
        # Optionally also write to file
        if out_file is not None:
            out_file.write(line + "\n")

    if is_dir:
        # -------- BATCH MODE: directory of instances --------
        if args.cnf:
            file_list = [
                os.path.join(inp_path, f)
                for f in os.listdir(inp_path)
                if f.endswith(".cnf")
            ]
        else:
            file_list = [
                os.path.join(inp_path, f)
                for f in os.listdir(inp_path)
                if os.path.isfile(os.path.join(inp_path, f))
            ]

        # Sort alphabetically (so uf50-01.cnf, uf50-02.cnf, ...)
        file_list.sort()

        # Limit number of instances if requested
        if args.limit is not None:
            file_list = file_list[:args.limit]

        # Header for the results table
        write("#file random dlcs jw mom")

        for path in file_list:
            results = run_on_instance(path, args.cnf)
            line = (
                f"{os.path.basename(path)} "
                f"{results['random']} {results['dlcs']} "
                f"{results['jw']} {results['mom']}"
            )
            write(line)

    else:
        # -------- SINGLE FILE MODE (your original behavior, just tidied) --------
        print(inp_path)  # keep your original print

        results = run_on_instance(inp_path, args.cnf)

        # Print each solver's status as before
        print(results["random"])
        print(results["dlcs"])
        print(results["jw"])
        print(results["mom"])

        # Optionally also log the result to a file in a one-line format
        if out_file is not None:
            out_file.write("#file random dlcs jw mom\n")
            out_file.write(
                f"{os.path.basename(inp_path)} {results['random']} "
                f"{results['dlcs']} {results['jw']} {results['mom']}\n"
            )

    if out_file is not None:
        out_file.close()


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
        print("Wrong file format! Expected first line to be 'p cnf NUM_VARS NUM_CLAUSES")
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

    if close:
        file.close()

    return clauses, num_vars


if __name__ == "__main__":
    main()
