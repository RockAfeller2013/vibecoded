# Apple Mac Studio Local LLM Test



The idea this script is to test a Local LLM on aApple Mac Studio and then cluster using more using EXO (https://github.com/exo-explore/exo), which I am postitive Apple will acquire and already intergrating. 

There are allot of youtube personabilities testing Mac 4 node cluster, but, none of them are actualy show a viable Code Quality and development process for real world apps. This script is to try and create a Base line and maybe even create some example Applications, or a sample Application / Prompt from a Single sthot to see if local LLM are good enough. The Power of Mac and architecture is alredy proven. This is how to actualy check if local LLM can produce a App compared to the frontiner models. 


## Research

-- https://chatgpt.com/c/6993ad05-3ccc-83a1-96c3-7120f8b0d6c8
-- https://claude.ai/chat/761c488a-097d-48f8-ac2b-4150a70ac6fb
- - https://chatgpt.com/c/6998e437-e274-839c-814e-1b120c749e9a
  - https://github.com/ggml-org/llama.cpp/discussions/4167
  - https://www.macstories.net/notes/notes-on-early-mac-studio-ai-benchmarks-with-qwen3-235b-a22b-and-qwen2-5-vl-72b/
  - https://blogs.novita.ai/llama-3-1-8b/#:~:text=Llama%203.1%208B%20Hardware%20Requirements%20Model%20VRAM,10.29%20GB%20RTX%203090%202%C3%97%20RTX%204060

## llama.cpp, Ollama, and MLX


llama.cpp, Ollama, and MLX

Llama 3.1 8B, Llama 3 8B
DeepSeek R1
Gemma-3-27b-q4
Qwen3-235B-A22B 
MacStories
MacStories
 +2

## Proompt to create the script



```

Create a **self-contained command-line script** that:

1. **Installs Ollama** if it is not already installed (macOS or Windows).
2. **Prompts the user to choose a model**:

   * `qwen2.5-coder:32b` (high-end machine)
   * `qwen2.5-coder:7b` (standard laptop)
   * `gemma:2b` (lightweight)
3. **Downloads the selected model** using Ollama.
4. **Starts Ollama in the background** and verifies the API is reachable at
   `http://localhost:11434/v1`.
5. **Sets the environment variable**
   `ANTHROPIC_BASE_URL=http://localhost:11434/v1`
   for the current shell session.
6. Checks whether `claude-code` is installed; if not, installs it.
7. Creates a new folder called `local-ai-test-app` containing:

   * a simple Python CLI app (`app.py`)
   * a minimal README
8. **Runs a test Claude Code prompt locally** using the selected model to:

   * generate a small Python example app (for example: a TODO CLI tool with add/list/remove commands)
   * write the generated files into the folder
9. Prints clear status messages for each step and exits with an error if any step fails.
9. Scipt needs to run on Apple Mac Studio / OSX using Bash only.

Constraints:

* The script must be runnable from the command line in one step.
* Use safe checks before installing software.
* Ensure the script is idempotent (safe to run multiple times).
* Provide the **complete script** plus instructions on how to run it.

```

