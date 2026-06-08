# Codegen Pipeline — Architecture Diagram

```mermaid
flowchart TD
    A([👤 You — Pi Console\nCtrl+G or /codegen]) --> B

    subgraph PI ["🖥️  Pi TUI Console"]
        B[Parse intent\n+ load AGENTS.md context]
        B --> C
        C{Extension\nrouter}
    end

    subgraph PIPELINE ["⚙️  LangGraph Pipeline  pipeline.py"]

        subgraph NODE1 ["Node 1 — Prompt Engineer"]
            D["🧠 Claude Sonnet\nclaude-sonnet-4-20250514\n\n• Reads AGENTS.md stack context\n• Crafts precise coding prompt\n• On retry: refines with Codex findings"]
        end

        subgraph NODE2 ["Node 2 — Code Generator"]
            E["💻 qwen3-coder:30b\nOllama — local & free\n\n• Receives Claude's engineered prompt\n• Generates production code\n• Never leaves your machine"]
        end

        subgraph NODE3 ["Node 3 — Code Reviewer"]
            F["🔍 Codex-1  OpenAI o3-based\n\n• Checks bugs + logic errors\n• Security vulnerabilities\n• Framework conventions\n• Ends: VERDICT PASSED / FAILED"]
        end

        subgraph NODE4 ["Node 4 — Decision"]
            G{Passed?}
        end

        D --> E
        E --> F
        F --> G
    end

    subgraph OUTPUTS ["📁  pipeline_output/"]
        H["generated_code.py\nengineer_prompt.md\nreview.md\nstatus.json"]
    end

    subgraph STACKS ["🗂️  Stack Context  AGENTS.md"]
        I["Python / FastAPI\nLaravel PHP\nJoomla CMS\nArchitecture rules\nSecurity requirements\nCode style standards"]
    end

    C --> D
    I -->|injected at session start| D

    G -->|"✅ PASSED"| J["Post final code\nto Pi conversation"]
    J --> K([✅ Done])

    G -->|"❌ FAILED\nattempts < 3"| L["Re-engineer prompt\nwith Codex findings"]
    L -->|loop back| D

    G -->|"❌ FAILED\nattempts = 3"| M["⚠️  Intervention\nDialog in Pi TUI"]
    M --> N{You choose}

    N -->|"Show Codex review"| O["Review findings\nposted to Pi chat"]
    N -->|"Show generated code"| P["Code posted\nto Pi chat"]
    N -->|"Show prompt"| Q["Engineered prompt\nposted to Pi chat"]
    N -->|"Dismiss"| R["Edit files manually\nin pipeline_output/"]

    O & P & Q & R --> S([🔄 Refine intent\nand re-run /codegen])

    G --> OUTPUTS
    M --> OUTPUTS

    style PI       fill:#1a1a2e,color:#e0e0ff,stroke:#4444aa
    style PIPELINE fill:#0d1f0d,color:#c0ffc0,stroke:#226622
    style NODE1    fill:#1a1035,color:#d0c0ff,stroke:#6644bb
    style NODE2    fill:#0d2020,color:#a0ffd0,stroke:#229966
    style NODE3    fill:#201010,color:#ffc0a0,stroke:#bb4422
    style NODE4    fill:#1a1a1a,color:#ffffff,stroke:#666666
    style OUTPUTS  fill:#1a1610,color:#ffe0a0,stroke:#aa8822
    style STACKS   fill:#101a1a,color:#a0e0ff,stroke:#226688

    style A fill:#2244aa,color:#ffffff,stroke:#4466cc
    style K fill:#226622,color:#ffffff,stroke:#44aa44
    style S fill:#884400,color:#ffffff,stroke:#aa6600
    style M fill:#882200,color:#ffffff,stroke:#cc4400
```

## Model Roles

| Stage | Model | Provider | Cost | Why |
|---|---|---|---|---|
| **Prompt Engineer** | claude-sonnet-4-20250514 | Anthropic API | ~$3/M tokens | Best meta-reasoning, understands mixed stacks |
| **Code Generator** | qwen3-coder:30b | Ollama — local | Free | Strong coding model, runs privately on your machine |
| **Code Reviewer** | codex-1 (o3-based) | OpenAI API | Premium | Specialist software engineering model, deep bug detection |

## Loop Behaviour

| Outcome | What happens |
|---|---|
| **PASSED** | Code posted directly into Pi conversation |
| **FAILED — attempt 1 or 2** | Claude re-engineers the prompt using Codex's specific findings |
| **FAILED — attempt 3** | Pi pauses and shows intervention dialog — you inspect and decide |

## Key Files

```
codegen-pipeline/
├── pipeline/pipeline.py          ← LangGraph pipeline (4 nodes)
├── pipeline/.env                 ← API keys + model config
├── pi-extension/codegen-pipeline.ts  ← Pi TUI integration
├── pi-skill/SKILL.md             ← natural language trigger
└── agents/AGENTS.md              ← your stack context (copy to project root)
```
