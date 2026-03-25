import tempfile
import subprocess
import os
import shutil

def render_manim_video(code: str, class_name: str = "GeneratedScene") -> tuple[str, str]:
    """
    Write the manim code to a temporary file, run Manim via subprocess,
    and return the path to the generated video file.
    
    Returns:
        tuple (video_path, error_logs)
    """
    # Create a temporary directory for the manim project to isolate environments
    temp_dir = tempfile.mkdtemp()
    
    # Write code to a file
    script_path = os.path.join(temp_dir, "scene.py")
    with open(script_path, "w") as f:
        f.write(code)
    
    # Output path
    output_dir = os.path.join(temp_dir, "media")
    
    # Construct manim command
    # -ql: quality low for faster rendering. You can change to -qh for high resolution.
    # --media_dir: overrides default media directory location to our temp folder.
    cmd = [
        "manim",
        "render",
        script_path,
        class_name,
        "-ql", 
        "--media_dir", output_dir
    ]
    
    try:
        # Run the simulation
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=temp_dir)
        logs = result.stdout + "\n" + result.stderr
        
        # Search for the generated mp4 video explicitly
        video_path = _find_mp4(output_dir)
        
        if result.returncode != 0 or not video_path:
            return None, logs
            
        return video_path, logs
    except Exception as e:
        return None, str(e)


def _find_mp4(directory: str) -> str:
    """Find the first .mp4 file in the given directory (recursively)."""
    if not os.path.exists(directory):
        return None
        
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith(".mp4"):
                return os.path.join(root, file)
    return None
