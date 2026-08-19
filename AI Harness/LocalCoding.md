 like asking questions. I used to do that in University(surprisingly didn't drive the professors crazy :D vice-versa they seemed to be excited about the chance to answer), in meeting rooms, on conferences. Now I do that on my podcast and for my upcoming newsletter.

A couple of days ago, I asked people to share their experience of moving from proprietary subscription-based models to local ones. I honestly wasn't aiming for gathering content-material, but it just happened so that a lot of people answered and answered quite honestly and enthusiastically. 

I think this question managed to gather the least toxic part of LinkedIn to share their real experiences and I wanted to summarize that in a separate post.

Here's what I asked

People who have switched from Claude Code to local models, how are you? What's your hardware configuration? Are you happy? Please share 🙏 
Who Actually Switched?
From around 100 comments, I could filter ~25 substantive answers and here are the results

Full replacement: 2–3 people fully replaced Claude Code with local models and most left for ethical reasons, not technical ones.

Everyone else landed on the same hybrid pattern independently: 

frontier models for reasoning, planning, and unfamiliar problems; 
local models for scoped, repeatable, "boring" work. 

Subscriptions for discovery, local for automating what's understood.

Interesting statistics

The numbers in the thread
~25 substantive replies, ~20 with concrete hardware specs
Qwen is the runaway default: ~12 setups (mostly the 27B coding model, some the 35B-A3B MoE for parallel threads). Gemma 4 second with ~5 mentions (26B/31B). Nobody's daily driver is Llama or Mistral. :/ 
The sweet spot everyone converged on: 20–30B params, quantized to 4-bit, on either 32–128GB Apple Silicon or a 16–24GB VRAM GPU.
DGX Spark-class boxes (Spark / ASUS GX10 / Ascent) appeared in 7 setups, the clear emerging prosumer category. Verdict split: three happy, one augmenting, one returning it.
Reported speeds: 16–30 tok/s is the typical usable range; one dual-Xeon setup runs GLM 5.2 at "a few tps" with 30–60 minute prompt waits.
At least 7 commenters built their own agent harness, and several admitted they use Claude to build the harness that runs the local model. Off-the-shelf harnesses mentioned: Hermes (3x), Pi / Oh My Pi (3x), OpenCode (2x), Ollama, MLX.
Best capability calibration: "Qwen 3.8 on a laptop 4090 is mostly on par with Haiku." and "as good as a very smart intern, but superhumanly fast."
Interesting cost report - for 640GB of local RAM across 3 machines: $50–100/month in electricity.

Popular hardware setups, grouped
Apple Silicon - Most Commont - ~9 SETUPS
MacBook Pro M3 · 36GB
M3 Max · 128GB
M3 Ultra · 256GB unified
Mac mini M4 · 32GB
M5 Max / M5 Pro · 48GB
M1 Max · 32GB

Single consumer GPU
RTX 5090
RTX 3090
Laptop RTX 4090 · 16GB VRAM
RX 7900 XTX · 24GB

DGX Spark class - ~7 SETUPS
DGX Spark
2x ASUS GX10
GX10 + 2x RTX A6000 on EPYC

Budget
Ryzen 7 2700X · 64GB DDR4 · RTX 5060 Ti + RTX 3060
Dual Xeon · 512GB DDR4 · RTX 4090

Highlights worth mentioning
"Switched" was the wrong verb. The real answer is task splitting. Don't expect "your own personal Claude", instead - tight scoped tasks (phishing scoring, alt-text generation)

Local models' one superpower over Claude: pinning. Frontier models change behavior on upgrade and break your prompts, while a local model is frozen and predictable

The harness: the most committed local-model people are using Claude to build the tooling that lets them use Claude less. 

Local coding: "gets the job done but 20x slower and more error prone."

Most popular reasons people switch: privacy first, learning second.

Personal thoughts
I think running the model locally gives you a very good understanding what are the models really good at, what's their real use-case as opposed to some unreliable "magic" the subscription models are supposedly giving you.

Data privacy and security questions are absolutely worth switching to local models whenever you work with sensitive data. (which is pretty much all the time?..)

Know your use-case, manage your expectations. The more "known" the problem is, the easier it'll be to create a "stricter" pipeline around it and achieve good results with local ones. 

If anyone wants to follow the answers themselves, without the interpretation layer - here's the link

https://www.linkedin.com/pulse/switching-from-claude-code-alike-local-models-nune-isabekyan-aittf/
