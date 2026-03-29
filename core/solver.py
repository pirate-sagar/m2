"""
Nonlinear Systems Solver using SymPy.

Parses equations, solves them numerically with Newton's method,
and records the full iteration history for animation.

Supports N-variable systems (2, 3, 4, … variables).
"""

import numpy as np
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class NewtonStep:
    """One iteration of Newton's method."""
    iteration: int
    point: tuple[float, ...]
    residual: float  # ||F(x)||


@dataclass
class SolutionResult:
    """Complete result of solving a nonlinear system."""
    equations_latex: list[str]           # LaTeX strings for each equation
    equations_raw: list[str]             # Raw string equations
    variables: list[str]                 # Variable names
    solutions: list[tuple[float, ...]]   # Found solutions
    newton_history: list[list[NewtonStep]]  # Iteration history per solution
    system_type: str                     # e.g. "polynomial", "trigonometric", "mixed"
    x_range: tuple[float, float]         # Plot range (primary axis)
    y_range: tuple[float, float]
    z_range: tuple[float, float] = (-6.0, 6.0)
    success: bool = True
    error_message: str = ""


def newton_method_nd(
    f_funcs: list,
    j_funcs: list[list],
    x0: list[float],
    tol: float = 1e-10,
    max_iter: int = 100,
) -> list[NewtonStep]:
    """
    Run Newton's method for an N-variable system and record every step.

    Args:
        f_funcs: list of N callables, each taking N floats -> float
        j_funcs: N×N list-of-lists of callables (the Jacobian)
        x0: initial guess (length N)
        tol: convergence tolerance on ||F(x)||
        max_iter: maximum iterations
    """
    n = len(x0)
    steps = []
    x = np.array(x0, dtype=float)

    for i in range(max_iter):
        fx = np.array([f(*x) for f in f_funcs], dtype=float)
        residual = float(np.linalg.norm(fx))
        steps.append(NewtonStep(iteration=i, point=tuple(x), residual=residual))

        if residual < tol:
            break

        # Build Jacobian matrix
        J = np.array([[j(*x) for j in row] for row in j_funcs], dtype=float)

        try:
            det = np.linalg.det(J)
            if abs(det) < 1e-14:
                # Singular Jacobian — can't continue
                break
            delta = np.linalg.solve(J, -fx)
        except np.linalg.LinAlgError:
            break

        # Damped Newton step: if step is very large, limit it
        step_norm = np.linalg.norm(delta)
        if step_norm > 10.0:
            delta = delta * (10.0 / step_norm)

        x = x + delta

    # Add final point if we have a different position
    fx = np.array([f(*x) for f in f_funcs], dtype=float)
    residual = float(np.linalg.norm(fx))
    if len(steps) == 0 or steps[-1].point != tuple(x):
        steps.append(NewtonStep(iteration=len(steps), point=tuple(x), residual=residual))

    return steps


def solve_system_from_parsed(parsed: dict) -> SolutionResult:
    """
    Given Gemini's parsed output (equations, variables, initial guesses, etc.),
    solve the system numerically and return full results.

    Supports 2, 3, 4, … variable systems.

    Expected `parsed` dict format:
    {
        "equations": ["x**2 + y**2 - 25", "y - x**2"],
        "equations_latex": ["x^2 + y^2 = 25", "y = x^2"],
        "variables": ["x", "y"],
        "initial_guesses": [[3.0, 4.0], [-3.0, 4.0]],
        "system_type": "polynomial",
        "x_range": [-6, 6],
        "y_range": [-6, 6],
        "z_range": [-6, 6]  # optional for 3D
    }
    """
    import sympy as sp

    equations_raw = parsed.get("equations", [])
    equations_latex = parsed.get("equations_latex", equations_raw)
    var_names = parsed.get("variables", ["x", "y"])
    initial_guesses = parsed.get("initial_guesses", [[1.0] * len(var_names)])
    system_type = parsed.get("system_type", "general")
    x_range = tuple(parsed.get("x_range", [-6, 6]))
    y_range = tuple(parsed.get("y_range", [-6, 6]))
    z_range = tuple(parsed.get("z_range", [-6, 6]))

    n_vars = len(var_names)
    n_eqs = len(equations_raw)

    is_ode = parsed.get("is_ode", False)
    if is_ode:
        # For ODEs, we do not solve for roots. We just return success 
        # so the pipeline can generate Manim scripts for the ODE.
        return SolutionResult(
            equations_latex=equations_latex,
            equations_raw=equations_raw,
            variables=var_names,
            solutions=[tuple(initial_guesses[0])] if initial_guesses else [],
            newton_history=[],
            system_type=system_type,
            x_range=x_range,
            y_range=y_range,
            z_range=z_range,
            success=True,
            error_message="ODE system. Numerical solution is handled in animation."
        )

    if n_eqs < n_vars:
        return SolutionResult(
            equations_latex=equations_latex,
            equations_raw=equations_raw,
            variables=var_names,
            solutions=[],
            newton_history=[],
            system_type=system_type,
            x_range=x_range,
            y_range=y_range,
            z_range=z_range,
            success=False,
            error_message=f"Under-determined system: {n_eqs} equations for {n_vars} variables.",
        )

    # Create sympy symbols
    symbols = sp.symbols(" ".join(var_names))
    if n_vars == 1:
        symbols = (symbols,)  # ensure it's a tuple

    try:
        # Parse string expressions into sympy expressions
        exprs = [sp.sympify(eq) for eq in equations_raw]
    except Exception as e:
        return SolutionResult(
            equations_latex=equations_latex,
            equations_raw=equations_raw,
            variables=var_names,
            solutions=[],
            newton_history=[],
            system_type=system_type,
            x_range=x_range,
            y_range=y_range,
            z_range=z_range,
            success=False,
            error_message=f"Failed to parse equations: {e}",
        )

    # Compute Jacobian symbolically (N x N matrix)
    jacobian_sym = [[sp.diff(expr, sym) for sym in symbols] for expr in exprs]

    # Lambdify for fast numerical evaluation
    f_funcs = [sp.lambdify(symbols, expr, modules=["numpy"]) for expr in exprs]
    j_funcs = [
        [sp.lambdify(symbols, jacobian_sym[i][j], modules=["numpy"]) for j in range(n_vars)]
        for i in range(n_eqs)
    ]

    # Run Newton's method from each initial guess
    solutions = []
    all_histories = []

    for guess in initial_guesses:
        # Pad or trim guess to match variable count
        g = list(guess)
        while len(g) < n_vars:
            g.append(1.0)
        g = g[:n_vars]

        history = newton_method_nd(
            f_funcs=f_funcs,
            j_funcs=j_funcs,
            x0=g,
        )
        all_histories.append(history)

        # Check convergence
        if history and history[-1].residual < 1e-6:
            sol = history[-1].point
            # Avoid duplicates (same solution from different initial guesses)
            is_duplicate = False
            for existing in solutions:
                if all(abs(a - b) < 1e-4 for a, b in zip(sol, existing)):
                    is_duplicate = True
                    break
            if not is_duplicate:
                solutions.append(sol)

    return SolutionResult(
        equations_latex=equations_latex,
        equations_raw=equations_raw,
        variables=var_names,
        solutions=solutions,
        newton_history=all_histories,
        system_type=system_type,
        x_range=x_range,
        y_range=y_range,
        z_range=z_range,
        success=len(solutions) > 0,
        error_message="" if solutions else "Newton's method did not converge. Try different initial guesses.",
    )
