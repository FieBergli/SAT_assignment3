"""
SAT Assignment Part 2 - Non-consecutive Sudoku Solver (Puzzle -> SAT/UNSAT)

THIS is the file to edit.

Implement: solve_cnf(clauses) -> (status, model_or_None)"""


from typing import Iterable, List, Tuple, Set, Dict
from collections import deque
import time


def convert_clauses(clauses: Iterable[Iterable[int]]) -> List[Tuple[int,...]]:
    """
    Convert clauses into an indexed, immutable representation suitable for
    watched-literals propagation.

    - Each clause becomes a tuple of ints (literals). Tuples are cheap to
      copy and index and we can iterate them fast.
    - We DO NOT expand clauses into sets here because the watched-literal
      logic iterates clause literals and needs a stable ordering/indexing.
    """
    return [tuple(c) for c in clauses]

# --------------------
# Simplification rules
# --------------------

def unit_clause_rule(clauses: List[Tuple[int,...]], assignment: Dict[int,bool]):
    """
    Unit propagation implemented using watched literals.

    Input:
      - clauses: list of clauses, each clause is a tuple of integers (literals).
                 e.g. (1, -5, 12)
      - assignment: dict mapping variable -> bool (partial assignment).
                    e.g. {1: True, 3: False}

    Output:
      - simplified_clauses: a list of frozenset clauses with falsified literals removed
                            and satisfied clauses removed (so the rest of code can continue).
      - assignment: updated assignment (may have more variables assigned by unit propagation)
      - conflict: bool, True if a conflict was detected.

    NOTES:
      - This function uses a watched-literal table. It performs unit propagation
        **without** scanning all clauses on every new assignment.
      - It returns the simplified clause set as a list of frozensets so the rest of
        your solver can operate as before.
    """

    # -------------------------
    # Helper subroutines
    # -------------------------
    def lit_is_true(lit: int, asgn: Dict[int,bool]) -> bool:
        """Return True if literal `lit` is known true by current assignment."""
        v = abs(lit)
        if v not in asgn:
            return False
        return asgn[v] == (lit > 0)

    def lit_is_false(lit: int, asgn: Dict[int,bool]) -> bool:
        """Return True if literal `lit` is known false by current assignment."""
        v = abs(lit)
        if v not in asgn:
            return False
        return asgn[v] != (lit > 0)

    # -------------------------
    # Build watches
    # -------------------------
    n_clauses = len(clauses)

    # For each clause index, we store the two watched literal positions (i, j).
    # If the clause has length 1 we will store the same literal twice (i == j).
    watched_pos: List[Tuple[int,int]] = []
    # watchers: map literal -> set of clause indices that currently watch that literal.
    watchers: Dict[int, Set[int]] = {}

    # queue for propagation: we store **literals that became TRUE** (not variables).
    # When a literal lit becomes true, clauses that watch -lit may need to update.
    queue = deque()

    # initialize data structures
    for ci, clause in enumerate(clauses):
        L = len(clause)
        if L == 0:
            # empty clause -> immediate conflict
            return clauses, assignment, True

        # choose first two literal positions to watch, or duplicate if only one literal
        if L == 1:
            i1 = 0
            i2 = 0
        else:
            i1 = 0
            i2 = 1

        watched_pos.append((i1, i2))

        # register watchers for those two literals
        for pos in (i1, i2):
            lit = clause[pos]
            watchers.setdefault(lit, set()).add(ci)

    # If the current assignment already contains variables, enqueue their
    # true-literals so we propagate their effects.
    for var, val in list(assignment.items()):
        lit = var if val else -var
        queue.append(lit)

    # Also find initial unit clauses and enqueue their required literal
    for ci, clause in enumerate(clauses):
        if len(clause) == 1:
            lit = clause[0]
            var = abs(lit)
            val = (lit > 0)
            # If variable already assigned inconsistently -> conflict
            if var in assignment and assignment[var] != val:
                return clauses, assignment, True
            if var not in assignment:
                assignment[var] = val
                queue.append(lit)

    # -------------------------
    # Main propagation loop
    # -------------------------
    while queue:
        true_lit = queue.popleft()
        # If assignment contradicts the queued literal, conflict
        v = abs(true_lit)
        desired_val = (true_lit > 0)
        if v in assignment and assignment[v] != desired_val:
            # This situation is unlikely because we check conflicts on assignment,
            # but it can happen if two queued unit literals contradict.
            return clauses, assignment, True

        # Clauses that watch -true_lit may be affected, because -true_lit is now false.
        affected_watch_list = list(watchers.get(-true_lit, set()))
        # NOTE: we copy the list because we'll modify the watchers dict while iterating.
        for ci in affected_watch_list:
            clause = clauses[ci]
            i1, i2 = watched_pos[ci]
            # determine which watched position corresponds to -true_lit
            # Because we might have duplicate positions in 1-literal clauses, handle generically.
            if clause[i1] == -true_lit:
                false_watch_pos = i1
                other_watch_pos = i2
            elif clause[i2] == -true_lit:
                false_watch_pos = i2
                other_watch_pos = i1
            else:
                # Clause no longer watching -true_lit (maybe changed earlier) -> skip
                continue

            other_lit = clause[other_watch_pos]

            # If the other watched literal is true, clause is satisfied -> nothing to do.
            if lit_is_true(other_lit, assignment):
                # No need to move the watch; clause is already satisfied.
                continue

            # Try to find a new literal in clause to watch (one that is not false)
            found_new_watch = False
            for idx, cand in enumerate(clause):
                if idx == other_watch_pos or idx == false_watch_pos:
                    continue
                # candidate is ok if it is not currently assigned false
                if not lit_is_false(cand, assignment):
                    # move watch from false_watch_pos -> idx
                    # 1) remove clause index from watchers[-true_lit]
                    watchers[-true_lit].discard(ci)
                    # 2) add clause index to watchers[cand]
                    watchers.setdefault(cand, set()).add(ci)
                    # 3) update watched positions for the clause
                    if false_watch_pos == i1:
                        watched_pos[ci] = (idx, other_watch_pos)
                    else:
                        watched_pos[ci] = (other_watch_pos, idx)
                    found_new_watch = True
                    break

            if found_new_watch:
                # We successfully moved the false watch to another literal; the clause
                # is now safe from immediate conflict.
                continue

            # Could not find a new watch: the clause only has the "other_lit"
            # as a candidate (or all other literals are false). Two cases:
            # - other_lit is unassigned -> unit clause -> assign it true
            # - other_lit is assigned false -> conflict
            if lit_is_false(other_lit, assignment):
                # clause is unsatisfiable under current partial assignment -> conflict
                return clauses, assignment, True

            # other_lit must be unassigned (since it's not true and not false)
            ov = abs(other_lit)
            oval = (other_lit > 0)
            # assign the variable and enqueue
            if ov in assignment:
                # if already assigned to different value -> conflict (shouldn't happen due to checks)
                if assignment[ov] != oval:
                    return clauses, assignment, True
            else:
                assignment[ov] = oval
                queue.append(other_lit)
                # Note: Do not change watchers here. The clause remains watching other_lit
                # (and the false watch is still -true_lit which we attempted to move and failed).
                # The effect of newly assigning other_lit will be handled when that literal
                # is popped from the queue (and we will process clauses watching -other_lit).
                # We do NOT remove or rebuild clauses here.

    # -------------------------
    # After propagation: build simplified clause list to return
    # -------------------------
    simplified = []
    for clause in clauses:
        # if any literal in clause is true -> clause satisfied -> skip it
        skip_clause = False
        new_clause_lits = []
        for lit in clause:
            if lit_is_true(lit, assignment):
                skip_clause = True
                break
            if not lit_is_false(lit, assignment):
                # keep unassigned literals
                new_clause_lits.append(lit)
            # if lit is false, we drop it (we do not include it in new_clause_lits)
        if skip_clause:
            continue
        if len(new_clause_lits) == 0:
            # empty clause -> conflict
            return clauses, assignment, True
        # store as frozenset so rest of your solver can use set operations if needed
        simplified.append(frozenset(new_clause_lits))

    # return the simplified clause list and updated assignment
    return simplified, assignment, False


def pure_literal_rule(clauses, assignment):
    clauses = clauses[:]
    assignment = dict(assignment)

    while True:
      pos_occ: Dict[int,int] = {}
      neg_occ: Dict[int,int] = {}
      
      for c in clauses:
        for lit in c:
          var = abs(lit)
          # already assigned variable, so skip
          if var in assignment:
            continue
          # add positive literal to the dict
          if lit > 0:
            pos_occ[var] = pos_occ.get(var,0) + 1
          # add negative literal to the dict
          else:
            neg_occ[var] = neg_occ.get(var,0) + 1

      pure_vars = []
      for var in set(list(pos_occ.keys()) + list(neg_occ.keys())):
        # already assigned, so continue
        if var in assignment:
          continue
        p = pos_occ.get(var,0)
        n = neg_occ.get(var,0)
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
    pos_score = {}
    neg_score = {}

    for c in clauses:
        # every clause gets a weight dependend on it's length
        weight = 2 ** (-len(c))
        # loop through literals in clause
        for lit in c:
            var = abs(lit)
            # already assigned, so skip
            if var in assignment:
                continue
            # add the positive scores of the variable
            if lit > 0:
                pos_score[var] = pos_score.get(var, 0.0) + weight
            # add the negative scores of the variable
            else:
                neg_score[var] = neg_score.get(var, 0.0) + weight

    # pick best variable
    best_var = None
    best_score = -1.0
    best_pref = True

    for var in range(1, num_vars + 1):
        # already assigned, so skip
        if var in assignment:
            continue
        p = pos_score.get(var, 0.0)
        n = neg_score.get(var, 0.0)
        score = p + n
        # update best score
        if score > best_score:
            best_score = score
            best_var = var
            best_pref = (p >= n)

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

def dpll(clauses, assignment, num_vars):
    """Recursive DPLL."""
    # 1. Unit clause rule
    clauses, assignment, conflict = unit_clause_rule(clauses, assignment)
    if conflict:
        return False, {}
    
    # 2. Pure literal elimination
    clauses, assignment = pure_literal_rule(clauses, assignment)

    # 3. Check base cases
    if not clauses:
        # no clauses -> satisfied
        return True, assignment
    if check_empty_clause(clauses):
        return False, {}

    # 4. Choose variable to split (heuristic)
    var, pref_val = split(clauses, assignment, num_vars)
    # if all variables already assigned, but not all clauses satisfied
    if var is None:
      return False, {}

    # 5. SPlit: try preferred polarity first
    for try_val in (pref_val, not pref_val):
      lit = var if try_val else -var
      
      new_assignment = dict(assignment)
      new_assignment[var] = try_val
      new_clauses = simplify_after_assignment(clauses, lit)
      # if empty clause, not satisfied,backtrack, try oher value
      if any(len(c) == 0 for c in new_clauses):
        continue
      # recursion, move to next level in our tree
      sat, final_assignment = dpll(new_clauses, new_assignment, num_vars)
      if sat:
        return True, final_assignment

    return False, {}

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

def solve_cnf(clauses, num_vars):
    """
    Implement your SAT solver here.
    Must return:
      ("SAT", model)  where model is a list of ints (DIMACS-style), or
      ("UNSAT", None)
    """
  
    clause_sets = convert_clauses(clauses)
    t0 = time.perf_counter()
    sat, assignment = dpll(clause_sets, {}, num_vars)
    t1 = time.perf_counter()
    runtime = t1 - t0
    print(f"Runtime JW watched: {runtime}")
    if sat:
      model = build_model(assignment, num_vars)
      return "SAT", model
    else:
      return "UNSAT", None

# python main.py --in puzzle.txt
# command to run in terminal: python3 main.py --in ../"EXAMPLE puzzles (input)"/example_n9.txt  --out example.cnf

