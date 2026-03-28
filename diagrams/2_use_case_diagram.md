# Use Case Diagram — Nonlinear Systems Solver

> Illustrates the actors (User, Gemini AI, Manim Engine) and the use cases they participate in.

```mermaid
flowchart LR
    subgraph Actors
        User((" User"))
        Gemini((" Gemini AI"))
        Manim((" Manim Engine"))
    end

    subgraph System[" Nonlinear Systems Solver"]
        UC1["UC1: Enter Nonlinear\nSystem Problem"]
        UC2["UC2: Select Example\nProblem"]
        UC3["UC3: Parse Natural\nLanguage to Equations"]
        UC4["UC4: Solve System\nNumerically"]
        UC5["UC5: Generate Manim\nAnimation Code"]
        UC6["UC6: Render Animation\nVideo"]
        UC7["UC7: Fix Broken\nManim Code"]
        UC8["UC8: View Solution\nAnimation"]
        UC9["UC9: View Solution\nDetails & Iterations"]
        UC10["UC10: View Generated\nCode & Logs"]
        UC11["UC11: Configure\nAPI Key"]
    end

    User --> UC1
    User --> UC2
    User --> UC8
    User --> UC9
    User --> UC10
    User --> UC11

    UC1 -->|"includes"| UC3
    UC2 -->|"includes"| UC1
    UC3 -->|"includes"| UC4
    UC4 -->|"includes"| UC5
    UC5 -->|"includes"| UC6
    UC6 -->|"extends"| UC7
    UC7 -->|"retries"| UC6

    Gemini --> UC3
    Gemini --> UC5
    Gemini --> UC7

    Manim --> UC6
```

## Use Case Descriptions

| ID   | Use Case                        | Actor(s)         | Description                                                                                     |
|------|----------------------------------|------------------|-------------------------------------------------------------------------------------------------|
| UC1  | Enter Nonlinear System Problem   | User             | User types a natural language description of a nonlinear system into the text input              |
| UC2  | Select Example Problem           | User             | User clicks a pre-defined example (2-var, 3-var, or 4-var system) to auto-fill the input         |
| UC3  | Parse Natural Language           | Gemini AI        | Gemini analyzes the prompt and extracts equations, variables, initial guesses, and ranges         |
| UC4  | Solve System Numerically         | System           | Newton's method is applied with multiple initial guesses to find all solutions                    |
| UC5  | Generate Manim Animation Code    | Gemini AI        | Gemini generates a complete Manim scene based on the parsed system and solution data              |
| UC6  | Render Animation Video           | Manim Engine     | Manim subprocess compiles the Python code into an MP4 video                                      |
| UC7  | Fix Broken Manim Code            | Gemini AI        | On render failure, Gemini analyzes error logs and produces corrected code (up to 3 retries)       |
| UC8  | View Solution Animation          | User             | User watches the auto-playing rendered video showing curves, Newton iterations, and solutions     |
| UC9  | View Solution Details            | User             | User reads the solution coordinates, iteration tables, and system analysis in the details panel   |
| UC10 | View Generated Code & Logs       | User             | User expands the accordion to inspect generated Manim code and render logs                       |
| UC11 | Configure API Key                | User             | User sets `GEMINI_API_KEY` in the `.env` file for the system to authenticate with Google Gemini   |
