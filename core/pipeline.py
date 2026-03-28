"""
Pipeline: orchestrates the full solve-and-animate workflow.

Flow: User prompt → Parse → Solve → Generate Animation → Render → (Retry on failure)
"""

import os
import time
from dataclasses import dataclass
from typing import Optional

from core.agent import analyze_nonlinear_system, generate_solution_animation, fix_manim_code
from core.solver import solve_system_from_parsed, SolutionResult
from core.manim_engine import render_manim_video


@dataclass
class PipelineResult:
    """The complete output of the pipeline."""
    video_path: Optional[str] = None
    solution: Optional[SolutionResult] = None
    parsed_system: Optional[dict] = None
    generated_code: str = ""
    render_logs: str = ""
    attempts: int = 0
    total_time: float = 0.0
    error: str = ""
    success: bool = False


def run_pipeline(
    user_prompt: str,
    max_retries: int = 3,
    progress_callback=None,
) -> PipelineResult:
    """
    Full pipeline: parse → solve → animate → render, with retries.
    
    Args:
        user_prompt: The user's natural language question
        max_retries: How many times to retry on render failure
        progress_callback: Optional callable(step_name, detail) for UI updates
    """
    result = PipelineResult()
    start_time = time.time()

    def update(step: str, detail: str = ""):
        if progress_callback:
            progress_callback(step, detail)

    # ── Step 1: Parse the system using Gemini ──
    update("Analyzing", "Parsing your equations with Gemini AI...")
    try:
        parsed = analyze_nonlinear_system(user_prompt)
        result.parsed_system = parsed
        update("Analyzing", f"Found system: {parsed.get('description', 'nonlinear system')}")
    except Exception as e:
        result.error = f"Failed to parse the system: {e}"
        result.total_time = time.time() - start_time
        return result

    # ── Step 2: Solve numerically with SymPy + Newton's method ──
    update("Solving", "Running Newton's method...")
    try:
        solution = solve_system_from_parsed(parsed)
        result.solution = solution

        if solution.success:
            sols_str = ", ".join(
                    "(" + ", ".join(f"{v:.4f}" for v in s) + ")" for s in solution.solutions
                )
            update("Solving", f"Found {len(solution.solutions)} solution(s): {sols_str}")
        else:
            update("Solving", f"Solver note: {solution.error_message}. Will still generate visual.")
    except Exception as e:
        # Solver failure is non-fatal — we can still generate an animation
        update("Solving", f"Numerical solver encountered an issue: {e}. Continuing with animation.")
        result.solution = SolutionResult(
            equations_latex=parsed.get("equations_latex", []),
            equations_raw=parsed.get("equations", []),
            variables=parsed.get("variables", ["x", "y"]),
            solutions=[],
            newton_history=[],
            system_type=parsed.get("system_type", "general"),
            x_range=tuple(parsed.get("x_range", [-6, 6])),
            y_range=tuple(parsed.get("y_range", [-6, 6])),
            success=False,
            error_message=str(e),
        )

    # ── Step 3: Generate Manim animation code ──
    update("Generating", "Creating animation code with Gemini AI...")
    try:
        code = generate_solution_animation(
            parsed_system=parsed,
            solutions=result.solution.solutions if result.solution else [],
            newton_histories=result.solution.newton_history if result.solution else [],
        )
        result.generated_code = code
        update("Generating", f"Generated {len(code.splitlines())} lines of Manim code")
    except Exception as e:
        result.error = f"Failed to generate animation code: {e}"
        result.total_time = time.time() - start_time
        return result

    # ── Step 4: Render with retries ──
    for attempt in range(1, max_retries + 1):
        result.attempts = attempt
        update("Rendering", f"Attempt {attempt}/{max_retries} — running Manim...")

        video_path, logs = render_manim_video(result.generated_code)
        result.render_logs = logs

        if video_path and os.path.exists(video_path):
            result.video_path = video_path
            result.success = True
            update("Complete", f"Video rendered successfully on attempt {attempt}!")
            break
        else:
            update("Fixing", f"Attempt {attempt} failed. Asking Gemini to fix the code...")
            if attempt < max_retries:
                try:
                    fixed_code = fix_manim_code(result.generated_code, logs)
                    result.generated_code = fixed_code
                    update("Fixing", "Code fixed. Retrying render...")
                except Exception as e:
                    update("Fixing", f"Fix attempt failed: {e}")

    if not result.success:
        result.error = "All render attempts failed. See logs for details."
        update("Failed", result.error)

    result.total_time = time.time() - start_time
    return result
