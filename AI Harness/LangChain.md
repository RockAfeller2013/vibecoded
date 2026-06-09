# LangChain

If You Want a 100% Open-Source Stack

You can use:

LangChain
LangGraph
LangServe
Deep Agents

and replace LangSmith with alternatives such as Langfuse, Laminar, or OpenTelemetry-based observability stacks. Community discussions consistently identify LangSmith as the primary proprietary component in the ecosystem.

For a self-hosted enterprise deployment in 2026, the most common open-source combination is:

LangGraph + LangChain + FastAPI + PostgreSQL + Langfuse rather than using LangSmit

| Product             | Purpose                                                                             | Open Source?                     | License / Availability                                          |
| ------------------- | ----------------------------------------------------------------------------------- | -------------------------------- | --------------------------------------------------------------- |
| LangChain           | Core framework for building LLM apps, agents, RAG, tools, and workflows             | Yes                              | MIT License ([langchain.com][1])                                |
| LangGraph           | Stateful agent workflows, multi-agent systems, human-in-the-loop, durable execution | Yes                              | MIT License (core framework) ([langchain.com][2])               |
| LangSmith           | Tracing, debugging, evaluation, prompt management, deployment                       | No                               | Proprietary SaaS / commercial product ([LangChain Docs][3])     |
| LangServe           | Expose LangChain/LangGraph apps as REST APIs                                        | Yes                              | Open source ([Adaptive Query][4])                               |
| LangChain Core      | Base abstractions for models, prompts, messages, runnables                          | Yes                              | MIT License ([Adaptive Query][4])                               |
| LangChain Community | Community-maintained integrations for databases, models, APIs                       | Yes                              | Open source ([Adaptive Query][4])                               |
| LangChain Hub       | Shared prompts, chains, templates                                                   | Yes                              | Open source/community platform ([Educative][5])                 |
| Deep Agents         | Pre-built agent architecture on top of LangGraph                                    | Yes                              | Open source ([langchain.com][2])                                |
| LangGraph Studio    | Visual development and debugging for LangGraph                                      | Partially                        | Free tooling, tied to LangGraph ecosystem ([LangChain Docs][3]) |
| LangGraph Platform  | Production deployment, scaling, scheduling, persistence                             | No                               | Commercial platform ([LangChain Docs][3])                       |
| SmithDB             | Specialized database backend for LangSmith                                          | No                               | Proprietary LangSmith component ([Reddit][6])                   |
| Context Hub         | Shared memory, skills, policies, context management                                 | No (currently LangSmith feature) | Proprietary platform feature ([Reddit][6])                      |

[1]: https://www.langchain.com/langchain?utm_source=chatgpt.com "LangChain: Open Source AI Agent Framework | Build Agents Faster"
[2]: https://www.langchain.com/blog/nvidia-enterprise?utm_source=chatgpt.com "LangChain Announces Enterprise Agentic AI Platform Built with NVIDIA"
[3]: https://docs.langchain.com/langgraph-platform/faq?utm_source=chatgpt.com "Frequently asked questions - Docs by LangChain"
[4]: https://qu3ry.net/articles/agent-schema/langchain-langgraph?utm_source=chatgpt.com "LangChain and LangGraph Agent Framework"
[5]: https://www.educative.io/blog/is-langchain-open-source?utm_source=chatgpt.com "Is LangChain available as open source?"
[6]: https://www.reddit.com/r/LangChain/comments/1te7byl/n_langchain_interrupt_2026_announcements_n/?utm_source=chatgpt.com "[N] LangChain Interrupt 2026 announcements [N]"

| Category            | Products                                                                          | Open Source? |
| ------------------- | --------------------------------------------------------------------------------- | ------------ |
| Core Frameworks     | LangChain, LangGraph, LangChain Core, LangChain Community, LangServe, Deep Agents | Yes          |
| Development Tools   | LangGraph Studio                                                                  | Partially    |
| Commercial Platform | LangSmith, LangGraph Platform, SmithDB, Context Hub                               | No           |
