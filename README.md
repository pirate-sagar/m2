# Math Animator Agent

An AI agent that takes user input and uses Gemini API to write Manim code, generating math animation videos.

## Requirements

### System Requirements
Manim requires some system dependencies to compile and render videos correctly.

#### **macOS**
You can install them using Homebrew:
```bash
brew install pkg-config cairo pango dbus ffmpeg
```
*(Optional)* For rendering LaTeX in the animations, you will also need a TeX distribution like MacTeX:
```bash
brew install --cask mactex-no-gui
```

#### **Linux (Ubuntu/Debian)**
Install system development headers and FFmpeg via APT:
```bash
sudo apt update
sudo apt install libcairo2-dev libpango1.0-dev pkg-config ffmpeg
```
*(Optional)* For rendering LaTeX in the animations:
```bash
sudo apt install texlive texlive-latex-extra texlive-fonts-extra texlive-latex-recommended texlive-science tipa
```

#### **Windows**
On Windows, most Python packages come with pre-built binaries, but you still need FFmpeg for rendering. You can install it using `winget`:
```powershell
winget install gyan.ffmpeg
```
*(Optional)* For rendering LaTeX in the animations, install MiKTeX:
```powershell
winget install MiKTeX.MiKTeX
```

### Python Requirements
To set up the project locally, run the following to initialize a virtual environment and install dependencies:
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Configuration
Copy the environment example file and add your Gemini API key:
```bash
cp .env.example .env
```
Edit `.env` and set `GEMINI_API_KEY="your_api_key_here"`.

## Running the App
Once everything is configured, run the Gradio interface:
```bash
python app.py
```
Open the provided local URL (usually `http://127.0.0.1:7860/`) in your browser.
