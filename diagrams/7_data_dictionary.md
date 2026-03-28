# Data Dictionary — Nonlinear Systems Solver

> Comprehensive reference of all data structures, their fields, types, constraints, and descriptions used throughout the application.

---

## 1. `NewtonStep` — Single Iteration Record

**Source:** `core/solver.py` (line 16)
**Type:** `@dataclass`

| Field       | Type              | Constraints         | Description                                        |
|-------------|-------------------|---------------------|----------------------------------------------------|
| `iteration` | `int`             | ≥ 0                 | Zero-based iteration index                         |
| `point`     | `tuple[float, ...]` | Length = N variables | Current point coordinates at this iteration         |
| `residual`  | `float`           | ≥ 0                 | `‖F(x)‖` — Euclidean norm of the system at `point` |

---

## 2. `SolutionResult` — Numerical Solver Output

**Source:** `core/solver.py` (line 24)
**Type:** `@dataclass`

| Field             | Type                          | Default           | Description                                                  |
|-------------------|-------------------------------|-------------------|--------------------------------------------------------------|
| `equations_latex` | `list[str]`                   | —                 | LaTeX-formatted equation strings for display                 |
| `equations_raw`   | `list[str]`                   | —                 | SymPy-compatible expression strings (set = 0)                |
| `variables`       | `list[str]`                   | —                 | Variable names, e.g. `["x", "y"]` or `["x", "y", "z"]`       |
| `solutions`       | `list[tuple[float, ...]]`     | —                 | List of converged solution points (deduplicated)              |
| `newton_history`  | `list[list[NewtonStep]]`      | —                 | One iteration history list per initial guess                 |
| `system_type`     | `str`                         | —                 | Classification: `polynomial`, `trigonometric`, `exponential`, `mixed` |
| `x_range`         | `tuple[float, float]`         | —                 | Plot range for x-axis                                        |
| `y_range`         | `tuple[float, float]`         | —                 | Plot range for y-axis                                        |
| `z_range`         | `tuple[float, float]`         | `(-6.0, 6.0)`     | Plot range for z-axis (used in 3D+ systems)                  |
| `success`         | `bool`                        | `True`            | Whether at least one solution converged                      |
| `error_message`   | `str`                         | `""`              | Error details if solver failed                               |

---

## 3. `PipelineResult` — Full Pipeline Output

**Source:** `core/pipeline.py` (line 18)
**Type:** `@dataclass`

| Field            | Type                     | Default  | Description                                                  |
|------------------|--------------------------|----------|--------------------------------------------------------------|
| `video_path`     | `Optional[str]`          | `None`   | Absolute path to the rendered `.mp4` animation file          |
| `solution`       | `Optional[SolutionResult]` | `None` | Numerical solver results (solutions + Newton history)         |
| `parsed_system`  | `Optional[dict]`         | `None`   | Gemini-parsed system (equations, variables, guesses, ranges) |
| `generated_code` | `str`                    | `""`     | Complete Manim Python source code (may be fixed version)      |
| `render_logs`    | `str`                    | `""`     | Combined stdout/stderr from Manim render subprocess           |
| `attempts`       | `int`                    | `0`      | Number of render attempts made (1–3)                          |
| `total_time`     | `float`                  | `0.0`    | Total pipeline execution time in seconds                      |
| `error`          | `str`                    | `""`     | Top-level error message (empty if successful)                 |
| `success`        | `bool`                   | `False`  | `True` if video was successfully rendered                     |

---

## 4. `parsed_system` — Gemini Parse Output (dict)

**Source:** Returned by `core/agent.py::analyze_nonlinear_system()`

| Key               | Type                    | Required | Default                | Description                                              |
|--------------------|-------------------------|----------|------------------------|----------------------------------------------------------|
| `equations`        | `list[str]`             |  Yes   | —                      | SymPy expressions set = 0 (e.g., `"x**2 + y**2 - 25"`)    |
| `equations_latex`  | `list[str]`             | No       | Same as `equations`    | Human-readable LaTeX forms (e.g., `"x^2 + y^2 = 25"`)     |
| `variables`        | `list[str]`             |  Yes   | —                      | Variable names (`["x", "y"]`, `["x", "y", "z"]`, etc.)    |
| `initial_guesses`  | `list[list[float]]`     |  Yes   | —                      | 4–10 starting points spread across solution regions        |
| `system_type`      | `str`                   | No       | `"general"`            | One of: `polynomial`, `trigonometric`, `exponential`, `mixed` |
| `x_range`          | `list[float, float]`    | No       | `[-6, 6]`              | Suggested x-axis range for plotting                        |
| `y_range`          | `list[float, float]`    | No       | `[-6, 6]`              | Suggested y-axis range for plotting                        |
| `z_range`          | `list[float, float]`    | No       | `[-6, 6]`              | Suggested z-axis range (3D systems only)                   |
| `description`      | `str`                   | No       | `"Nonlinear system..."` | Brief natural language description of the system          |

---

## 5. Gemini API Configuration

**Source:** `core/agent.py`

| Parameter             | Type     | Value                        | Description                                 |
|-----------------------|----------|------------------------------|---------------------------------------------|
| `model`               | `str`    | `"gemini-3.1-pro-preview"`   | Gemini model identifier                     |
| `temperature`         | `float`  | `0.1` (parse) / `0.2` (gen) | Controls randomness of AI output             |
| `thinking_level`      | `str`    | `"HIGH"`                     | Enables deep reasoning in Gemini             |
| `GEMINI_API_KEY`      | `str`    | From `.env` file             | Google AI API authentication key             |

---

## 6. Newton's Method Parameters

**Source:** `core/solver.py::newton_method_nd()`

| Parameter   | Type           | Default  | Description                                   |
|-------------|----------------|----------|-----------------------------------------------|
| `f_funcs`   | `list[callable]` | —      | N lambdified system functions                  |
| `j_funcs`   | `list[list[callable]]` | — | N×N lambdified Jacobian matrix                |
| `x0`        | `list[float]`  | —        | Initial guess point (length N)                 |
| `tol`       | `float`        | `1e-10`  | Convergence tolerance on `‖F(x)‖`             |
| `max_iter`  | `int`          | `100`    | Maximum Newton iterations per guess            |
| Damping     | —              | `10.0`   | Step norm is clamped to 10.0 if exceeded       |
| Singularity | —              | `1e-14`  | Jacobian determinant threshold for singularity |
| Dedup tol   | —              | `1e-4`   | Tolerance for considering two solutions equal  |
| Convergence | —              | `1e-6`   | Final residual threshold for "converged"       |

---

## 7. Manim Engine Configuration

**Source:** `core/manim_engine.py::render_manim_video()`

| Parameter     | Type   | Default            | Description                                |
|---------------|--------|--------------------|--------------------------------------------|
| `code`        | `str`  | —                  | Complete Manim Python source code           |
| `class_name`  | `str`  | `"GeneratedScene"` | Name of the Manim Scene class to render     |
| Quality flag  | `str`  | `"-ql"`            | Low quality for fast rendering              |
| `media_dir`   | `str`  | `<temp>/media`     | Output directory for rendered media files    |

---

## 8. Gradio UI Components

**Source:** `app.py`

| Component         | Type            | Description                                          |
|--------------------|-----------------|------------------------------------------------------|
| `prompt_input`     | `gr.Textbox`    | Multi-line text input for the problem description    |
| `generate_btn`     | `gr.Button`     | Primary "Solve & Animate" action button              |
| `example_btns`     | `list[gr.Button]` | 12 pre-defined example problem buttons             |
| `video_output`     | `gr.Video`      | Auto-playing video player for solution animation     |
| `solution_info`    | `gr.Markdown`   | Solution details: equations, solutions, iterations   |
| `code_output`      | `gr.Markdown`   | Generated Manim code and render logs                 |
| `EXAMPLES`         | `list[str]`     | 12 example prompts (6 × 2-var, 4 × 3-var, 2 × 4-var) |

---

## 9. Environment Variables

**Source:** `.env`

| Variable         | Type   | Required | Description                                  |
|------------------|--------|----------|----------------------------------------------|
| `GEMINI_API_KEY` | `str`  |  Yes   | Google Gemini API key for authentication     |

---

## 10. External Dependencies

**Source:** `requirements.txt`

| Package         | Version      | Purpose                                      |
|-----------------|-------------|-----------------------------------------------|
| `manim`         | `≥ 0.18.1`  | Mathematical animation engine                  |
| `gradio`        | `≥ 4.0.0`   | Web UI framework                               |
| `google-genai`  | Latest       | Google Gemini AI client library                 |
| `python-dotenv` | Latest       | Load environment variables from `.env`          |
| `sympy`         | `≥ 1.12`    | Symbolic mathematics (parsing & Jacobians)      |
| `numpy`         | `≥ 1.24.0`  | Numerical computation (Newton's method)         |
