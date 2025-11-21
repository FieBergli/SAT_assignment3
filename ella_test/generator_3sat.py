import random


def generate_random_3sat(num_vars, num_clauses, filename):
    with open(filename, "w") as f:
        # Header
        f.write(f"p cnf {num_vars} {num_clauses}\n")

        for _ in range(num_clauses):
            clause = set()
            while len(clause) < 3:
                var = random.randint(1, num_vars)
                lit = var if random.choice([True, False]) else -var
                clause.add(lit)
            # Write clause
            f.write(" ".join(str(l) for l in clause) + " 0\n")


generate_random_3sat(num_vars=50, num_clauses=210, filename="random_3sat.cnf")
