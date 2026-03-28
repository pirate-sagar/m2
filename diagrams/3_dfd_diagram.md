# DFD — Nonlinear Systems Solver

> Data Flow Diagrams showing how data moves between processes, data stores, and external entities.

---

## Level 0 — Context Diagram

```mermaid
flowchart LR
    User((" User"))
    System[" Nonlinear Systems\nSolver"]
    GeminiAPI[("️ Gemini API")]
    FileSystem[(" File System\n(Temp Videos)")]

    User -->|"Natural language\nproblem description"| System
    User -->|"Example selection"| System
    System -->|"Solution video (MP4)"| User
    System -->|"Solution details\n& iteration tables"| User
    System -->|"Generated code\n& render logs"| User

    System <-->|"Parse request /\nParsed JSON"| GeminiAPI
    System <-->|"Code generation request /\nManim Python code"| GeminiAPI
    System <-->|"Code fix request /\nFixed code"| GeminiAPI

    System -->|"Write temp .py file"| FileSystem
    FileSystem -->|"Rendered .mp4 video"| System
```

---

## Level 1 — Detailed Data Flow

```mermaid
flowchart TB
    User((" User"))
    GeminiAPI[("️ Gemini API")]
    TempFS[(" Temp File System")]
    EnvFile[(" .env File")]

    subgraph P0["app.py — Gradio UI"]
        UI_Input["1.0 Receive User\nInput"]
        UI_Output["1.1 Display\nResults"]
    end

    subgraph P1["core/agent.py — AI Agent"]
        Parse["2.0 analyze_nonlinear_system\nParse NL → JSON"]
        GenCode["2.1 generate_solution_animation\nCreate Manim Code"]
        FixCode["2.2 fix_manim_code\nDebug & Fix Code"]
    end

    subgraph P2["core/solver.py — Numerical Solver"]
        Solve["3.0 solve_system_from_parsed\nSymPy + Newton's Method"]
        Newton["3.1 newton_method_nd\nN-D Newton Iterations"]
    end

    subgraph P3["core/pipeline.py — Orchestrator"]
        Pipeline["4.0 run_pipeline\nOrchestrate Full Workflow"]
    end

    subgraph P4["core/manim_engine.py — Renderer"]
        Render["5.0 render_manim_video\nSubprocess Manim Render"]
        FindMP4["5.1 _find_mp4\nLocate Output Video"]
    end

    %% User flows
    User -->|"prompt text"| UI_Input
    UI_Output -->|"video, solution info,\ncode & logs"| User

    %% UI to Pipeline
    UI_Input -->|"prompt string"| Pipeline

    %% Pipeline orchestration
    Pipeline -->|"user_prompt"| Parse
    Parse -->|"parsed system dict\n(equations, vars, guesses)"| Pipeline
    Pipeline -->|"parsed system dict"| Solve
    Solve -->|"SolutionResult\n(solutions, newton_history)"| Pipeline
    Solve -->|"equations, Jacobian"| Newton
    Newton -->|"list of NewtonStep"| Solve
    Pipeline -->|"parsed_system, solutions,\nnewton_histories"| GenCode
    GenCode -->|"Manim Python code"| Pipeline
    Pipeline -->|"Manim code string"| Render
    Render -->|"video_path, logs"| Pipeline
    Pipeline -->|"code + error_logs"| FixCode
    FixCode -->|"fixed Manim code"| Pipeline

    %% Render details
    Render -->|"write .py file"| TempFS
    Render -->|"subprocess: manim render"| TempFS
    TempFS -->|".mp4 path"| FindMP4
    FindMP4 -->|"video_path"| Render

    %% External API calls
    Parse <-->|"prompt / JSON response"| GeminiAPI
    GenCode <-->|"system data / code response"| GeminiAPI
    FixCode <-->|"code + errors / fixed code"| GeminiAPI

    %% Env
    EnvFile -->|"GEMINI_API_KEY"| Parse
    EnvFile -->|"GEMINI_API_KEY"| GenCode
    EnvFile -->|"GEMINI_API_KEY"| FixCode

    %% Pipeline to UI
    Pipeline -->|"PipelineResult\n(video, solution, code, logs)"| UI_Output
```
