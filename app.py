"""
Gradio UI for the Nonlinear Systems Solver Agent.

A rich interface that shows:
- Video animation of the solution
- Parsed equations & description
- Newton iteration history
- Generated Manim code
"""

import gradio as gr
import os
from dotenv import load_dotenv

from core.pipeline import run_pipeline

load_dotenv()


EXAMPLES = [
    # ── 2-variable systems ──
    "Solve x² + y² = 25 and y = x²",
    "Find where the circle x² + y² = 4 intersects the line y = x + 1",
    "Solve the system: sin(x) + y = 1 and x² + y² = 4",
    "Where does the hyperbola xy = 6 meet the ellipse x²/9 + y²/4 = 1?",
    "Solve x³ - y = 0 and x + y³ = 2",
    "Find intersection of y = eˣ - 3 and y = ln(x) + 1",
    # ── 3-variable / 3-equation systems ──
    "Solve the 3-equation system: x² + y² + z² = 14, x + y + z = 6, and xz = y",
    "Find solutions to: x² + y = 10, y² + z = 10, z² + x = 10",
    "Solve: sin(x) + y + z = 1, x + sin(y) + z = 1, x + y + sin(z) = 1",
    "Solve the system: x*y - z = 0, y*z - x = 0, x*z - y = 0 with x² + y² + z² = 3",
    # ── 4-variable / complex systems ──
    "Solve: x² + y² = 1, y² + z² = 1, z² + w² = 1, w² + x² = 1",
    "Find where x + y + z + w = 4, xy + zw = 1, x² + y² + z² + w² = 6, and xyzw = 0.5",
]


def format_solution_info(result) -> str:
    """Build a rich markdown summary from the pipeline result."""
    lines = []

    # ── Status ──
    if result.success:
        lines.append(f"### Solved in {result.total_time:.1f}s ({result.attempts} render attempt{'s' if result.attempts > 1 else ''})\n")
    else:
        lines.append(f"### Failed after {result.total_time:.1f}s\n")
        if result.error:
            lines.append(f"**Error:** {result.error}\n")

    # ── System Description ──
    if result.parsed_system:
        p = result.parsed_system
        lines.append(f"---\n### System Analysis\n")
        lines.append(f"**Type:** {p.get('system_type', 'general').title()}\n")
        n_vars = len(p.get('variables', ['x', 'y']))
        n_eqs = len(p.get('equations', []))
        lines.append(f"**Dimension:** {n_vars} variables, {n_eqs} equations\n")
        lines.append(f"**Description:** {p.get('description', 'N/A')}\n")
        lines.append(f"\n**Equations:**\n")
        for eq in p.get("equations_latex", p.get("equations", [])):
            lines.append(f"- $${eq}$$\n")

    # ── Solutions ──
    if result.solution and result.solution.solutions:
        lines.append(f"\n---\n### Solutions Found: {len(result.solution.solutions)}\n")
        for i, sol in enumerate(result.solution.solutions):
            coords = ", ".join(f"{v} = {s:.6f}" for v, s in zip(result.solution.variables, sol))
            lines.append(f"**Solution {i+1}:** ({coords})\n")

    # ── Newton Iteration Table ──
    if result.solution and result.solution.newton_history:
        lines.append(f"\n---\n### Newton's Method Iterations\n")
        variables = result.solution.variables
        for g_idx, history in enumerate(result.solution.newton_history):
            if not history:
                continue
            init_pt = ", ".join(f"{history[0].point[k]:.4f}" for k in range(len(history[0].point)))
            lines.append(f"\n**From initial guess {g_idx+1}:** ({init_pt})\n")
            
            # Build table header dynamically based on number of variables
            header_vars = " | ".join(variables)
            header_sep = " | ".join("---" for _ in variables)
            lines.append(f"| Iter | {header_vars} | Residual |\n|------|{header_sep}|----------|\n")
            
            for step in history[:15]:
                var_vals = " | ".join(f"{step.point[k]:.6f}" for k in range(len(step.point)))
                lines.append(
                    f"| {step.iteration} | {var_vals} | {step.residual:.2e} |\n"
                )
            if history[-1].residual < 1e-6:
                lines.append(f"\n**Converged** at iteration {history[-1].iteration}\n")
            else:
                lines.append(f"\nDid not converge (final residual: {history[-1].residual:.2e})\n")

    return "".join(lines)


def format_code_section(result) -> str:
    """Format the generated code for display."""
    if not result.generated_code:
        return "No code was generated."

    lines = []
    lines.append("### Generated Manim Code\n\n")
    lines.append(f"```python\n{result.generated_code}\n```\n")

    if result.render_logs:
        lines.append("\n---\n### Render Logs\n\n")
        # Truncate very long logs
        logs = result.render_logs
        if len(logs) > 3000:
            logs = logs[:1500] + "\n\n... (truncated) ...\n\n" + logs[-1500:]
        lines.append(f"```\n{logs}\n```\n")

    return "".join(lines)


def solve_and_animate(prompt: str):
    """Main handler: run the full pipeline and return results for the UI."""
    if not prompt or not prompt.strip():
        return None, "Please enter a question about a nonlinear system.", ""

    if not os.getenv("GEMINI_API_KEY") or os.getenv("GEMINI_API_KEY") == "your_api_key_here":
        return None, "**GEMINI_API_KEY** is not set. Please configure it in your `.env` file.", ""

    result = run_pipeline(user_prompt=prompt.strip(), max_retries=3)

    video = result.video_path if result.success else None
    info = format_solution_info(result)
    code = format_code_section(result)

    return video, info, code


# ─── Build the Gradio Interface ─────────────────────────────────────

custom_css = """
/* ===== Respect the Gradio theme — no hardcoded dark backgrounds ===== */
.gradio-container {
    max-width: 100% !important;
    width: 100% !important;
}
.main-title {
    text-align: center;
    background: linear-gradient(135deg, #3b82f6 0%, #60a5fa 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    font-size: 2.8em;
    font-weight: 800;
    margin-bottom: 0;
    padding-bottom: 5px;
}
.subtitle {
    text-align: center;
    color: var(--body-text-color-subdued);
    font-size: 1.2em;
    margin-top: 5px;
}
.box-container {
    border: 1px solid var(--border-color-primary);
    border-radius: 12px;
    padding: 20px;
    background: var(--background-fill-secondary);
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -1px rgba(0, 0, 0, 0.03);
}
"""

theme_config = gr.themes.Soft(
    primary_hue="blue",
    secondary_hue="sky",
    neutral_hue="slate",
)

with gr.Blocks(
    title="Math Motion (m2)",
) as demo:

    gr.HTML("""
        <div style="text-align: center; padding: 20px 0 10px 0;">
            <h1 class="main-title">Math Motion (m2)</h1>
            <p class="subtitle">Describe a nonlinear system — AI will solve it and create a visual animation</p>
        </div>
    """)

    with gr.Row(equal_height=False):
        # ── Left Column: Input ──
        with gr.Column(scale=5, elem_classes=["box-container"]):
            gr.Markdown("### Enter Problem")
            prompt_input = gr.Textbox(
                label="",
                placeholder="e.g. 'Solve x² + y² = 25 and y = x²'\nor 'Solve x² + y² + z² = 14, x + y + z = 6, xz = y'",
                lines=5,
                max_lines=10,
                show_label=False,
            )
            generate_btn = gr.Button(
                "Solve & Animate",
                variant="primary",
                size="lg",
            )
            
            gr.Markdown("---")
            gr.Markdown("**Or try an example:**")
            example_btns = []
            for ex in EXAMPLES:
                btn = gr.Button(ex, variant="secondary", size="sm")
                btn.click(fn=lambda e=ex: e, outputs=[prompt_input])
                example_btns.append(btn)

        # ── Right Column: Video ──
        with gr.Column(scale=7):
            video_output = gr.Video(
                label="Solution Animation",
                autoplay=True,
                height=500,
            )

    # ── Bottom: Details ──
    with gr.Row():
        with gr.Column():
            with gr.Accordion("Solution Details", open=True):
                solution_info = gr.Markdown(
                    value="*Enter a problem above and click 'Solve & Animate' to get started.*"
                )
            with gr.Accordion("Generated Code & Logs", open=False):
                code_output = gr.Markdown(value="")

    # ── Wire it up ──
    generate_btn.click(
        fn=solve_and_animate,
        inputs=[prompt_input],
        outputs=[video_output, solution_info, code_output],
    )

    prompt_input.submit(
        fn=solve_and_animate,
        inputs=[prompt_input],
        outputs=[video_output, solution_info, code_output],
    )


if __name__ == "__main__":
    if not os.getenv("GEMINI_API_KEY") or os.getenv("GEMINI_API_KEY") == "your_api_key_here":
        print("Warning: GEMINI_API_KEY is not set. Please set it in your .env file.")
    demo.launch(theme=theme_config, css=custom_css)
