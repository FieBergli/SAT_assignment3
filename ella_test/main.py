#!/usr/bin/env python3
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


def parse_args():
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--in", dest="inp", required=True, help="Input file path")
    p.add_argument("--cnf", dest="cnf", action="store_true", help="Treat input as DIMACS CNF")
    return p.parse_args()


def main():

    args = parse_args()
    print(args.inp)

    if args.cnf:
        # DIMACS CNF file (random 3-SAT, SAT benchmarks)
        clauses, num_vars = read_dimacs(args.inp)
    else:
        # Sudoku puzzle text file
        clauses, num_vars = to_cnf(args.inp)

    status, _ = solve_cnf_random(clauses, num_vars)
    print(status)
    status, _ = solve_cnf_dlcs(clauses, num_vars)
    print(status)
    status, _ = solve_cnf_jw(clauses, num_vars)
    print(status)
    status, _ = solve_cnf_mom(clauses, num_vars)
    print(status)


def parse_dimacs(input_path: str) -> Tuple[Iterable[Iterable[int]], int]:
    close = False
    if isinstance(input_path, str):
        file = open(input_path, "r")
        close = True
    else:
        file = input_path


    line = file.readline()

    components = line.strip().split(" ")

    if len(components)!= 4 or components[0]!="p" or components[1]!="cnf":
      print("Wrong file format! Expected first line to be 'p cnf NUM_VARS NUM_CLAUSES")
      exit(1)

    num_vars=int(components[2])
    num_clauses=int(components[3])

    clauses=[]

    line=file.readline()
    while(line):
       numbers = [int(x) for x in line.strip().split(" ")]

       if(numbers[-1]!=0):
          print("Wrong format! Clause lines must be terminated with a 0")

       clauses.append(numbers[:-1])

       line=file.readline()


    return clauses, num_vars

if __name__ == "__main__":
   main()

# python3 main.py --in uf50-218/uf50-01.cnf --cnf