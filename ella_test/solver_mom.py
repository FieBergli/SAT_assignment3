"""
SAT Assignment Part 2 - Non-consecutive Sudoku Solver (Puzzle -> SAT/UNSAT)

THIS is the file to edit.

Implement: solve_cnf(clauses) -> (status, model_or_None)"""

from typing import Iterable, List, Tuple, Set, Dict
import time


def convert_clauses(clauses):
    """Convert clauses to a list-of-sets"""
    return [set(c) for c in clauses]


# --------------------
# Simplification rules
# --------------------


def unit_clause_rule(clauses, assignment):
    clauses = clauses[:]
    assignment = dict(assignment)

    while True:
        # find unit clauses
        unit_lits = []
        for c in clauses:
            if len(c) == 1:
                unit_lits.append(next(iter(c)))

        if not unit_lits:
            break

        for lit in unit_lits:
            # check boolean of literal
            var = abs(lit)
            val = lit > 0

            # check for conflict
            if var in assignment:
                if assignment[var] != val:
                    return clauses, assignment, True
                else:
                    continue

            # put variable in assignment
            assignment[var] = val

            # simplify clauses:
            new_clauses = []
            # loop through clauses and check if the contain the unit lit
            for c in clauses:
                # unit clause satisfied, so remove
                if lit in c:
                    continue
                # literal falsified, so remove
                if -lit in c:
                    new_c = set(c)
                    new_c.remove(-lit)
                    # empty clause, so conflict
                    if len(new_c) == 0:
                        return clauses, assignment, True
                    new_clauses.append(new_c)
                # unit literal not in clause
                else:
                    new_clauses.append(c)
            clauses = new_clauses

    return clauses, assignment, False


def pure_literal_rule(clauses, assignment):
    clauses = clauses[:]
    assignment = dict(assignment)

    while True:
        pos_occ: Dict[int, int] = {}
        neg_occ: Dict[int, int] = {}

        for c in clauses:
            for lit in c:
                var = abs(lit)
                # already assigned variable, so skip
                if var in assignment:
                    continue
                # add positive literal to the dict
                if lit > 0:
                    pos_occ[var] = pos_occ.get(var, 0) + 1
                # add negative literal to the dict
                else:
                    neg_occ[var] = neg_occ.get(var, 0) + 1

        pure_vars = []
        for var in set(list(pos_occ.keys()) + list(neg_occ.keys())):
            # already assigned, so continue
            if var in assignment:
                continue
            p = pos_occ.get(var, 0)
            n = neg_occ.get(var, 0)
            # add true pure variable
            if p > 0 and n == 0:
                pure_vars.append((var, True))
            # add false pure variable
            elif n > 0 and p == 0:
                pure_vars.append((var, False))

        if not pure_vars:
            break

        # assign and simplify
        for var, val in pure_vars:
            # assign pure literal
            assignment[var] = val
            # update the clauses
            lit = var if val else -var
            new_clauses = []
            for c in clauses:
                # clause is satisfied, so skip
                if lit in c:
                    continue
                # clause does not have pure literal so don't change
                new_clauses.append(c)
            clauses = new_clauses

    return clauses, assignment


# --------------------
# Split
# --------------------


def split(clauses, assignment, num_vars):
    """
    Chosen heuristic for splitting: Jeroslow Wang Two Sided

    """
    # filter out clauses that contain only unassigned variables
    unassigned_clauses = [
        c for c in clauses if not all(abs(l) in assignment for l in c)
    ]
    if not unassigned_clauses:
        return None, True

    # find the minimum clause length
    min_len = min(len(c) for c in unassigned_clauses)

    # collect only the shortest clauses
    min_clauses = [c for c in unassigned_clauses if len(c) == min_len]

    # count literal occurrences
    scores = {}
    for c in min_clauses:
        for lit in c:
            var = abs(lit)
            if var in assignment:
                continue
            scores[var] = scores.get(var, 0) + 1

    # pick variable with maximum score
    best_var = max(scores, key=scores.get)
    # choose preferred polarity = whichever appears more often
    pol_score = 0
    for c in min_clauses:
        if best_var in c:
            pol_score += 1
        if -best_var in c:
            pol_score -= 1

    # prefer polarity with highest occurrence
    best_pref = pol_score >= 0

    return best_var, best_pref


# --------------------
# Simplify
# --------------------
def check_empty_clause(clauses):
    return any(len(c) == 0 for c in clauses)


def simplify_after_assignment(clauses, lit):
    """
    Given assignment of literal `lit` to True, remove satisfied clauses and remove -lit from other clauses.
    """
    new_clauses = []
    for c in clauses:
        # clause satisfied, so skip
        if lit in c:
            continue
        # remove the negations of the literal from the clause
        if -lit in c:
            new_c = set(c)
            new_c.remove(-lit)
            new_clauses.append(new_c)
        # clause not affected by literal
        else:
            new_clauses.append(c)
    return new_clauses


# --------------------
# DPLL
# --------------------


def dpll(clauses, assignment, num_vars, counters):
    """Recursive DPLL."""
    counters["calls"] += 1
    # 1. Unit clause rule
    clauses, assignment, conflict = unit_clause_rule(clauses, assignment)
    if conflict:
        return False, {}, counters

    # 2. Pure literal elimination
    clauses, assignment = pure_literal_rule(clauses, assignment)

    # 3. Check base cases
    if not clauses:
        # no clauses -> satisfied
        return True, assignment, counters
    if check_empty_clause(clauses):
        return False, {}, counters

    # 4. Choose variable to split (heuristic)
    var, pref_val = split(clauses, assignment, num_vars)
    # if all variables already assigned, but not all clauses satisfied
    if var is None:
        return False, {}, counters

    # 5. SPlit: try preferred polarity first
    counters["splits"] += 1
    for try_val in (pref_val, not pref_val):
        lit = var if try_val else -var

        new_assignment = dict(assignment)
        new_assignment[var] = try_val
        new_clauses = simplify_after_assignment(clauses, lit)
        # if empty clause, not satisfied,backtrack, try oher value
        if any(len(c) == 0 for c in new_clauses):
            continue
        # recursion, move to next level in our tree
        sat, final_assignment, counters = dpll(
            new_clauses, new_assignment, num_vars, counters
        )
        if not sat:
            counters["backtracks"] += 1
        if sat:
            return True, final_assignment, counters

    return False, {}, counters


def build_model(assignment, num_vars):
    """
    Build a full DIMACS-style model
    Unassigned variables are set to False
    """
    model = []
    for v in range(1, num_vars + 1):
        val = assignment.get(v, False)
        model.append(v if val else -v)
    return model


def solve_cnf_mom(clauses, num_vars, log=False):
    """
    Solve a CNF formula using the Maximum Occurrences in clauses of Minimum Size (MOM) heuristic.
    Return:
      ("SAT", model)  where model is a list of ints (DIMACS-style), or
      ("UNSAT", None)
    """

    init_counters = {"splits": 0, "backtracks": 0, "calls": 0}

    clause_sets = convert_clauses(clauses)
    t0 = time.perf_counter()
    sat, assignment, counters = dpll(clause_sets, {}, num_vars, init_counters)
    t1 = time.perf_counter()
    runtime = t1 - t0

    string = ""

    string += f"Runtime MOM: {runtime}\n"
    string += f"Splits MOM: {counters['splits']}\n"
    string += f"Backtracks MOM: {counters['backtracks']}\n"
    string += f"Recursive calls MOM: {counters['calls']}\n"

    if log:
        print(string)

    if sat:
        model = build_model(assignment, num_vars)
        return "SAT", model, string
    else:
        return "UNSAT", None, string


# python main.py --in puzzle.txt
# command to run in terminal: python3 main.py --in ../"EXAMPLE puzzles (input)"/example_n9.txt  --out example.cnf
