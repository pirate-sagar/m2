"""
AI Agent powered by Gemini 3.1 Pro for nonlinear systems solving.

Two main capabilities:
1. Parse a user's natural language question into structured equations (N variables)
2. Generate Manim animation code using solution data
"""

import os
import json
import re
from google import genai
from google.genai import types


def _get_client():
    """Create a Gemini client."""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY is not set.")
    return genai.Client(api_key=api_key)


def analyze_nonlinear_system(user_prompt: str) -> dict:
    """
    Use Gemini to parse the user's natural language into a structured
    nonlinear system definition — supports 2, 3, 4, … variable systems.

    Returns a dict with:
    {
        "equations": ["x**2 + y**2 + z**2 - 14", "x + y + z - 6", "x*z - y"],
        "equations_latex": ["x^2 + y^2 + z^2 = 14", "x + y + z = 6", "xz = y"],
        "variables": ["x", "y", "z"],
        "initial_guesses": [[1.0, 2.0, 3.0], [2.0, 1.0, 3.0]],
        "system_type": "polynomial",
        "x_range": [-6, 6],
        "y_range": [-6, 6],
        "z_range": [-6, 6],
        "description": "A sphere, plane, and hyperbolic surface"
    }
    """
    client = _get_client()

    system_instruction = """You are a mathematical analysis assistant. The user will describe a nonlinear system of equations in natural language or mathematical notation.

Your job is to parse their input and return a JSON object with the following structure:

{
    "equations": ["expr1", "expr2", ...],
    "equations_latex": ["latex1", "latex2", ...],
    "variables": ["x", "y"] or ["x", "y", "z"] or ["x", "y", "z", "w"] etc.,
    "initial_guesses": [[x0, y0, ...], [x1, y1, ...], ...],
    "system_type": "polynomial|trigonometric|exponential|mixed",
    "x_range": [xmin, xmax],
    "y_range": [ymin, ymax],
    "z_range": [zmin, zmax],
    "description": "Brief description of what these curves/surfaces are"
}

CRITICAL RULES:
1. "equations" must contain SymPy-compatible expressions set equal to zero. For example, if the equation is "x^2 + y^2 = 25", write it as "x**2 + y**2 - 25". Use ** for exponents, not ^.
2. Use standard Python/SymPy math functions: sin, cos, tan, exp, log, sqrt, Abs, pi, E
3. "equations_latex" should be the human-readable LaTeX form (e.g., "x^2 + y^2 = 25")
4. "variables" can be 2, 3, 4, or more variables. Match the system's actual dimensionality.
   - The number of equations MUST equal the number of variables for Newton's method to work.
5. Provide 4-8 initial guesses spread across the expected solution regions. Think carefully about where solutions might be. This is CRITICAL for finding all solutions.
6. Set x_range, y_range, z_range to comfortably contain all expected solutions with some margin.
   - z_range is only needed for 3+ variable systems.
7. Return ONLY the JSON object, no markdown formatting, no explanation.
8. For systems with 3+ variables, be extra generous with initial guesses (try 6-10).
9. When a system has obvious symmetry, include initial guesses that exploit the symmetry to find all solution branches.

If the user gives a vague or underspecified request, pick a reasonable and interesting nonlinear system that demonstrates the concept they're asking about."""

    response = client.models.generate_content(
        model="gemini-3.1-pro-preview",
        contents=user_prompt,
        config=types.GenerateContentConfig(
            system_instruction=system_instruction,
            thinking_config=types.ThinkingConfig(
                thinking_level="HIGH",
            ),
            temperature=0.1,
        ),
    )
    
    text = response.text.strip()
    
    # Clean markdown wrappers if present
    if text.startswith("```json"):
        text = text[7:]
    if text.startswith("```"):
        text = text[3:]
    if text.endswith("```"):
        text = text[:-3]
    text = text.strip()

    try:
        parsed = json.loads(text)
    except json.JSONDecodeError as e:
        # Try to extract JSON from the response
        json_match = re.search(r'\{[\s\S]*\}', text)
        if json_match:
            parsed = json.loads(json_match.group())
        else:
            raise ValueError(f"Failed to parse Gemini response as JSON: {e}\nResponse: {text}")

    # Validate required fields
    required = ["equations", "variables", "initial_guesses"]
    for field in required:
        if field not in parsed:
            raise ValueError(f"Missing required field '{field}' in Gemini response")

    if "equations_latex" not in parsed:
        parsed["equations_latex"] = parsed["equations"]
    if "system_type" not in parsed:
        parsed["system_type"] = "general"
    if "x_range" not in parsed:
        parsed["x_range"] = [-6, 6]
    if "y_range" not in parsed:
        parsed["y_range"] = [-6, 6]
    if "z_range" not in parsed:
        parsed["z_range"] = [-6, 6]
    if "description" not in parsed:
        parsed["description"] = "Nonlinear system of equations"

    return parsed


def generate_solution_animation(
    parsed_system: dict,
    solutions: list,
    newton_histories: list,
) -> str:
    """
    Use Gemini to generate Manim code that visualizes the nonlinear system
    and the Newton's method solving process.

    Supports 2D and 3D systems.

    Returns the Manim Python code as a string.
    """
    client = _get_client()

    n_vars = len(parsed_system["variables"])

    # Format solution data for the prompt
    solutions_str = ""
    for i, sol in enumerate(solutions):
        coords = ", ".join(f"{v:.6f}" for v in sol)
        solutions_str += f"  Solution {i+1}: ({coords})\n"

    newton_str = ""
    for g_idx, history in enumerate(newton_histories):
        newton_str += f"\n  --- From initial guess {g_idx+1} ---\n"
        for step in history[:10]:  # Limit to 10 steps for prompt size
            coords = ", ".join(f"{v:.6f}" for v in step.point)
            newton_str += f"    Iteration {step.iteration}: ({coords}), residual={step.residual:.2e}\n"

    equations_display = "\n".join(f"  {i+1}. {eq}" for i, eq in enumerate(parsed_system.get("equations_latex", parsed_system["equations"])))
    variables_str = ", ".join(parsed_system["variables"])

    # Dynamic instructions based on dimensionality
    if n_vars == 2:
        plotting_instructions = f"""
3. **Plot the Curves** (~2-3 seconds):
   - Use `axes.plot_implicit_curve()` for each equation
   - Use distinct vibrant colors (e.g., "#FF6B6B" red, "#4ECDC4" teal, "#FFE66D" yellow, "#3B82F6" blue)
   - NEVER use purple or purple gradients
   - Add a small legend or equation label near each curve
   - Animate curves appearing with `Create()`

4. **Newton's Method Animation** (~4-6 seconds per solution):
   - For each solution found via Newton's method:
     a. Show the initial guess as a colored dot with label "x₀"
     b. Show an animated "step label" like "Iteration 1, 2, 3..."
     c. Animate arrows from each iteration point to the next
     d. Show the dot moving along the arrows
     e. Use decreasing opacity or changing color for each step
     f. When converged, flash the final point with a highlight effect

5. **Solution Highlight** (~2 seconds):
   - Mark each solution point with a glowing dot
   - Display the coordinates as LaTeX: "(x, y) = (value, value)"
   - Use `Circumscribe` or `Flash` effect on solution points

PLOTTING NOTES:
- Use 2D `Axes` with ranges [{parsed_system["x_range"][0]}, {parsed_system["x_range"][1]}] x [{parsed_system["y_range"][0]}, {parsed_system["y_range"][1]}]
- For `plot_implicit_curve`, the function signature is `lambda x, y: expression` where the curve is where expression = 0
"""
    elif n_vars == 3:
        plotting_instructions = f"""
3. **3D Visualization** (~3-4 seconds):
   - Use `ThreeDAxes` to create a 3D coordinate system
   - Show the equations as LaTeX in a corner of the screen
   - Use `Surface` or `ParametricFunction` where applicable to visualize constraint surfaces
   - If surfaces are hard to plot, just show the equations in LaTeX and focus on the solution points
   - Set camera angle with `self.set_camera_orientation(phi=75*DEGREES, theta=30*DEGREES)`
   - Gently rotate camera during the animation for a 3D effect using `self.begin_ambient_camera_rotation(rate=0.15)`

4. **Newton's Method Animation** (~4-6 seconds):
   - Show each initial guess as a 3D dot using `Dot3D`
   - Animate the convergence path as lines connecting iteration points
   - When converged, highlight the solution with `Flash`

5. **Solution Highlight** (~2 seconds):
   - Mark each solution with a glowing `Dot3D`
   - Display coordinates as LaTeX: "(x, y, z) = (v1, v2, v3)"

PLOTTING NOTES:
- Use `ThreeDScene` instead of `Scene` as the parent class, class name MUST be `GeneratedScene`
- Use `ThreeDAxes` with ranges x=[{parsed_system["x_range"][0]}, {parsed_system["x_range"][1]}], y=[{parsed_system["y_range"][0]}, {parsed_system["y_range"][1]}], z=[{parsed_system["z_range"][0]}, {parsed_system["z_range"][1]}]
- Use `axes.c2p(x, y, z)` for coordinate conversion in 3D
- Use `Dot3D(point=axes.c2p(x, y, z))` for 3D points
- Use `Line3D` for 3D lines between iteration points
"""
    else:
        # 4+ variables — can't visualize in 3D, use a text-based approach
        plotting_instructions = f"""
3. **Equations Display** (~3 seconds):
   - Since this is a {n_vars}-variable system, we cannot plot surfaces.
   - Display all equations beautifully in LaTeX, centered on screen.
   - Use `VGroup` to stack equations vertically with nice spacing.
   - Animate each equation appearing with `Write()`.

4. **Newton's Method Animation** (~4-6 seconds):
   - Create a table or list showing iteration progress.
   - Show the variables and residual changing over iterations.
   - Use `DecimalNumber` mobjects to show values updating.
   - Alternatively, show a horizontal bar chart of residual decreasing.

5. **Solution Display** (~3 seconds):
   - Show each solution as a nicely formatted LaTeX expression.
   - Flash or highlight each solution.
   - Show coordinate values to 4 decimal places.

PLOTTING NOTES:
- Use a standard `Scene` (not `ThreeDScene`).
- Focus on making the mathematical content beautiful and readable.
- Use animations to build up the information step by step.
"""

    system_instruction = f"""You are an expert Manim animator who creates beautiful, educational math animations.
You will generate a COMPLETE, SELF-CONTAINED Manim scene that visualizes solving a nonlinear system of equations.

CRITICAL REQUIREMENTS:
1. Import: `from manim import *`
2. Class name MUST be `GeneratedScene` inheriting from `{"ThreeDScene" if n_vars == 3 else "Scene"}`
3. Return ONLY valid, execution-ready Python code
4. NO markdown formatting (no ```python ... ```)
5. The animation MUST be visually stunning with smooth transitions
6. Use `config.frame_rate = 30` quality

THE NONLINEAR SYSTEM:
{equations_display}

System type: {parsed_system.get("system_type", "general")}
Description: {parsed_system.get("description", "")}
Variables: {variables_str} ({n_vars}-dimensional)
Plot x_range: {parsed_system["x_range"]}
Plot y_range: {parsed_system["y_range"]}
{"Plot z_range: " + str(parsed_system.get("z_range", [-6, 6])) if n_vars >= 3 else ""}

SOLUTIONS FOUND:
{solutions_str if solutions_str else "  No solutions converged (still animate the curves)"}

NEWTON'S METHOD ITERATION DATA:
{newton_str if newton_str else "  No iteration data available"}

ANIMATION STRUCTURE (follow this order):
1. **Title Card** (1-2 seconds):
   - Show "Solving {n_vars}D Nonlinear System" as a title with a gradient or color effect
   - Display the equations in LaTeX below the title
   - Fade everything out

2. **Coordinate System** (~1 second):
   - Create appropriate axes for the system dimensionality
   - Add axis labels
   - Use a clean, dark background aesthetic

{plotting_instructions}

6. **Summary Card** (~2 seconds):
   - Show a summary box with "Solutions:" header
   - List all solution coordinates
   - Show "Solved using Newton's Method" subtitle

STYLE GUIDELINES:
- Use `MathTex` for all math, not `Text`
- Use smooth animations: `Write`, `Create`, `FadeIn`, `FadeOut`, `Transform`
- Add `self.wait(0.5)` between major sections
- Use color constants or hex colors for a modern palette
- Keep the total animation under 25 seconds
- If plotting implicit curves, use reasonable step_size (0.05 to 0.1) for smooth curves
- Handle edge cases: if a curve equation uses sin/cos/exp, make sure to import numpy as np and use np.sin etc in lambda functions

AVOID THESE COMMON ERRORS:
- Don't use `axes.get_graph()` for implicit curves — use `axes.plot_implicit_curve()` 
- Don't reference variables before defining them
- Don't use `TexMobject` — use `MathTex` or `Tex`
- Don't forget `self.play()` — direct `self.add()` won't animate
- Make sure all coordinate transformations go through `axes.c2p()` (coords to point)
- For `plot_implicit_curve`, the function signature is `lambda x, y: expression` where the curve is where expression = 0
- For 3D scenes, use `ThreeDScene` as parent and `ThreeDAxes`
- For 3D dots, use `Dot3D`, not `Dot`
"""

    response = client.models.generate_content(
        model="gemini-3.1-pro-preview",
        contents=f"Generate the Manim animation code for the nonlinear system described in the system prompt. Make it visually beautiful and educational.",
        config=types.GenerateContentConfig(
            system_instruction=system_instruction,
            thinking_config=types.ThinkingConfig(
                thinking_level="HIGH",
            ),
            temperature=0.2,
        ),
    )
    
    code = response.text.strip()
    
    # Clean markdown wrappers
    if code.startswith("```python"):
        code = code[9:]
    if code.startswith("```"):
        code = code[3:]
    if code.endswith("```"):
        code = code[:-3]
    
    return code.strip()


def fix_manim_code(code: str, error_log: str) -> str:
    """
    Given broken Manim code and its error log, ask Gemini to fix it.
    Returns the corrected code.
    """
    client = _get_client()

    system_instruction = """You are a Manim debugging expert. The user will provide Manim code that failed to render, along with the error log.

Fix the code and return ONLY the corrected, complete Python code.
DO NOT include any markdown formatting (no ```python blocks).
DO NOT include any explanation — just the pure Python code.

The class name MUST remain `GeneratedScene`.
Import must be `from manim import *`.

Common fixes:
- `plot_implicit_curve` requires a function(x, y) -> value, curve is where value=0
- Use `axes.c2p(x, y)` for coordinate conversion
- `MathTex` not `TexMobject`
- Check that all variables are defined before use
- Make sure np is imported if using numpy functions
- `Axes` range format: x_range=[min, max, step], y_range=[min, max, step]
- For 3D scenes: inherit from `ThreeDScene`, use `ThreeDAxes`, `Dot3D`, `Line3D`
- For `Dot3D`, use `point=` keyword, not positional
- `set_camera_orientation` needs `phi=` and `theta=` keyword args
"""

    prompt = f"""This Manim code failed to render. Fix it.

CODE:
{code}

ERROR LOG:
{error_log}
"""

    response = client.models.generate_content(
        model="gemini-3.1-pro-preview",
        contents=prompt,
        config=types.GenerateContentConfig(
            system_instruction=system_instruction,
            thinking_config=types.ThinkingConfig(
                thinking_level="HIGH",
            ),
            temperature=0.1,
        ),
    )
    
    fixed = response.text.strip()
    if fixed.startswith("```python"):
        fixed = fixed[9:]
    if fixed.startswith("```"):
        fixed = fixed[3:]
    if fixed.endswith("```"):
        fixed = fixed[:-3]
    
    return fixed.strip()


def generate_manim_code(prompt: str) -> str:
    """
    Legacy function: Given a user prompt, ask Gemini to generate Manim code.
    Kept for backward compatibility.
    """
    client = _get_client()

    system_instruction = (
        "You are an expert at writing Manim code for generating math animations. "
        "Create a single class inheriting from Scene that fulfills the user's request. "
        "Return ONLY valid execution-ready python code, without any markdown formatting wrappers (like ```python ... ```). "
        "Make sure to import manim using `from manim import *` at the top. "
        "Make the animations visually beautiful, modern, and mathematically coherent. "
        "Ensure the default class name is always 'GeneratedScene'."
    )

    response = client.models.generate_content(
        model="gemini-3.1-pro-preview",
        contents=prompt,
        config=types.GenerateContentConfig(
            system_instruction=system_instruction,
            thinking_config=types.ThinkingConfig(
                thinking_level="HIGH",
            ),
            temperature=0.2,
        ),
    )
    code = response.text

    if code.startswith("```python"):
        code = code[9:]
    if code.startswith("```"):
        code = code[3:]
    if code.endswith("```"):
        code = code[:-3]

    return code.strip()
