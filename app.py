import gradio as gr
import os
from dotenv import load_dotenv

from core.agent import generate_manim_code
from core.manim_engine import render_manim_video

# Load environment variables from .env
load_dotenv()

def generate_video(prompt):
    # 1. Ask Gemini to write Manim code based on the prompt
    code = generate_manim_code(prompt)
    if not code:
        return None, "Failed to generate code. Please check your API key and network connection."
    
    # 2. Render Manim video locally
    video_path, logs = render_manim_video(code)
    
    # 3. Handle success and errors
    if video_path and os.path.exists(video_path):
        return video_path, f"Success! \n\n### Generated Code:\n```python\n{code}\n```"
    else:
        error_message = f"Rendering failed.\n\n### Error Logs:\n```text\n{logs}\n```\n\n### Generated Code:\n```python\n{code}\n```"
        return None, error_message

# Build the Gradio App interface
with gr.Blocks(title="Math Animator Agent", theme=gr.themes.Soft()) as demo:
    gr.Markdown("# 🎨 Math Animator Agent")
    gr.Markdown("Describe the math animation you want to generate, and Gemini will autonomously write the Manim code to create the video.")
    
    with gr.Row():
        with gr.Column(scale=1):
            prompt_input = gr.Textbox(
                label="What would you like to animate?", 
                placeholder="e.g. Draw a circle and then morph it into a square, with text explaining it.",
                lines=5
            )
            generate_btn = gr.Button("Generate Animation", variant="primary")
            log_output = gr.Markdown(label="Logs / Generated Code")
            
        with gr.Column(scale=1):
            video_output = gr.Video(label="Generated Animation")
            
    generate_btn.click(
        fn=generate_video,
        inputs=[prompt_input],
        outputs=[video_output, log_output]
    )

if __name__ == "__main__":
    if not os.getenv("GEMINI_API_KEY") or os.getenv("GEMINI_API_KEY") == "your_api_key_here":
        print("Warning: GEMINI_API_KEY environment variable is not set correctly. Please set it in your .env file.")
    # Launch Gradio interface
    demo.launch()
