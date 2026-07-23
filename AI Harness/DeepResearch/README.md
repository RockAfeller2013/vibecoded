# Deep Research 

- Provide resources books, website, pdfs, links
- Builds a Learning Wiki/Cloudlan/Jupiter Notebook
- Convert this to Agent Skills
- https://github.com/virgiliojr94/book-to-skill

# Open Source Deep Research Platform Comparison

## Goal

Build an open-source Deep Research platform comparable to ChatGPT Deep Research, Gemini Deep Research, or Perplexity Labs using self-hosted components and your own LLMs.

he end result is your own self-hosted Deep Research platform that works similarly to ChatGPT Deep Research or Gemini Deep Research, but with complete control over your data, models, and infrastructure. Instead of only searching the web, it can understand and reason across your internal documents, PDFs, Git repositories, websites, SharePoint, emails, notes, and other knowledge sources.

When you ask a question, the platform automatically gathers information from all connected sources, retrieves the most relevant content, performs multi-step reasoning with one or more LLMs, verifies and cites its sources, and produces a structured report. It can also compare documents, identify conflicting information, summarize findings, generate diagrams, and create deliverables such as Markdown, Word, PDF, or PowerPoint reports.

Over time, it becomes a central knowledge and research assistant for your organisation. Rather than searching individual systems manually, you ask questions in natural language and receive comprehensive, evidence-backed answers drawn from both your private knowledge and public information, while keeping everything under your control and running on open-source software.


Create a Jupiternote book 0r Wiki.js https://docs.requarks.io/comments
---

# 1. Open Source Deep Research Comparison

| Project | Purpose | Web Search | PDF | Office Docs | GitHub | Local Files | YouTube | OCR | RAG | Agents | Workflow | UI | Best Use |
|----------|----------|-----------|------|------------|--------|-------------|----------|-----|-----|--------|----------|-----|----------|
| Open WebUI | Complete AI UI | Yes | Yes | Yes | Yes | Yes | Yes | Yes | Yes | Yes | Pipelines | Excellent | Best overall frontend |
| AnythingLLM | Private knowledge base | Limited | Yes | Yes | Yes | Yes | Yes | OCR | Yes | Basic | No | Excellent | Enterprise RAG |
| LibreChat | Multi-LLM Chat | MCP/Search | Yes | Yes | Yes | Yes | Yes | OCR | Yes | MCP | Yes | Excellent | ChatGPT alternative |
| Dify | AI App Builder | Yes | Yes | Yes | Yes | Yes | Limited | OCR | Yes | Yes | Excellent | Excellent | Production AI apps |
| Flowise | Visual Agent Builder | Via tools | Yes | Yes | Yes | Yes | Yes | OCR | Yes | Excellent | Excellent | Good | No-code workflows |
| Langflow | LangChain Builder | Via tools | Yes | Yes | Yes | Yes | Yes | OCR | Yes | Excellent | Excellent | Good | Research workflows |
| LlamaIndex | Data Framework | Yes | Yes | Yes | Yes | Yes | Yes | OCR | Excellent | Yes | Code | None | Best RAG framework |
| Haystack | Enterprise RAG | Yes | Yes | Yes | Yes | Yes | Yes | OCR | Excellent | Yes | Pipelines | API | Enterprise search |
| OpenHands | Coding Agent | Limited | Yes | Yes | GitHub | Yes | No | No | Limited | Excellent | Yes | Good | Software engineering |
| CrewAI | Multi-agent | Yes | Yes | Yes | Yes | Yes | Yes | OCR | Yes | Excellent | Excellent | None | Autonomous research |
| AutoGen | Multi-agent | Yes | Yes | Yes | Yes | Yes | Yes | OCR | Yes | Excellent | Excellent | None | Complex agent systems |
| n8n | Workflow Automation | Excellent | Yes | Yes | Yes | Yes | Yes | OCR | Connectors | Yes | Excellent | Good | Automation |
| Semantic Kernel | Microsoft AI SDK | Via plugins | Yes | Yes | Yes | Yes | Yes | OCR | Yes | Excellent | Excellent | API | Enterprise AI |
| GraphRAG | Knowledge Graph RAG | No | Yes | Yes | Yes | Yes | No | OCR | Excellent | Limited | No | None | Complex document relationships |
| PrivateGPT | Local private GPT | No | Yes | Yes | Limited | Yes | No | OCR | Yes | No | No | Basic | Offline document chat |

---

# 2. Document Sources Your Research Platform Should Support

| Source | Supported | Notes |
|---------|-----------|------|
| PDFs | Yes | Manuals, books, research papers |
| Microsoft Word | Yes | DOCX |
| Excel | Yes | XLSX, CSV |
| PowerPoint | Yes | PPTX |
| Markdown | Yes | Documentation |
| Text Files | Yes | TXT, LOG |
| HTML | Yes | Web pages |
| Websites | Yes | Crawl or scrape |
| RSS Feeds | Yes | News |
| GitHub Repositories | Yes | Entire repositories |
| GitLab | Yes | Clone repositories |
| Confluence | Yes | Enterprise docs |
| SharePoint | Yes | Enterprise docs |
| Google Drive | Yes | Cloud storage |
| OneDrive | Yes | Cloud storage |
| Dropbox | Yes | Cloud storage |
| Box | Yes | Cloud storage |
| S3 Buckets | Yes | Object storage |
| Local Folder | Yes | Continuous indexing |
| Network Shares | Yes | SMB/NFS |
| YouTube Videos | Yes | Transcript extraction |
| Podcasts | Yes | Speech-to-text |
| Audio Files | Yes | Whisper transcription |
| Images | Yes | OCR + Vision |
| Screenshots | Yes | OCR |
| Scanned Documents | Yes | OCR |
| Emails | Yes | Outlook, IMAP |
| Slack | Yes | API integration |
| Teams | Yes | Graph API |
| Discord | Yes | Bot/API |
| Jira | Yes | REST API |
| Notion | Yes | API |
| Obsidian Vault | Yes | Markdown |
| Zotero | Yes | Research library |
| SQL Databases | Yes | Structured queries |
| PostgreSQL | Yes | SQL |
| MySQL | Yes | SQL |
| SQLite | Yes | SQL |
| Elasticsearch | Yes | Existing indexes |
| REST APIs | Yes | JSON |
| GraphQL APIs | Yes | Structured APIs |
| Local LLM Memory | Yes | Conversation history |

---

# 3. Data Ingestion Methods

| Method | Description |
|---------|-------------|
| Drag and Drop |
| Folder Monitoring |
| Scheduled Crawling |
| Git Clone |
| API Connectors |
| Browser Extension |
| Bookmark Import |
| RSS Monitoring |
| Email Forwarding |
| Webhook |
| CLI Upload |
| Mobile Upload |
| OCR Pipeline |
| Speech-to-Text |
| Batch Processing |

---

# 4. Required Processing Pipeline

```
Source
      │
      ▼
Document Loader
      │
      ▼
OCR (Optional)
      │
      ▼
Metadata Extraction
      │
      ▼
Document Chunking
      │
      ▼
Embeddings
      │
      ▼
Vector Database
      │
      ▼
Hybrid Search
      │
      ▼
Re-ranking
      │
      ▼
LLM Reasoning
      │
      ▼
Citation Generation
      │
      ▼
Report Generation
```

---

# 5. Open Source OCR

| Tool | Notes |
|------|------|
| Tesseract | Standard OCR |
| PaddleOCR | Excellent accuracy |
| EasyOCR | Python-based |
| OCRmyPDF | Searchable PDFs |
| Surya OCR | Modern document OCR |
| DocTR | Deep Learning OCR |
| Microsoft TrOCR | Transformer OCR |

---

# 6. Embedding Models

| Model | Quality | Local |
|---------|---------|-------|
| BAAI BGE-M3 | Excellent | Yes |
| Nomic Embed Text | Excellent | Yes |
| Snowflake Arctic Embed | Excellent | Yes |
| Jina Embeddings v3 | Excellent | Yes |
| e5-large-v2 | Excellent | Yes |
| mxbai-embed-large | Excellent | Yes |

---

# 7. Vector Databases

| Database | Open Source | Scale |
|------------|------------|-------|
| Qdrant | Yes | Excellent |
| Milvus | Yes | Excellent |
| Weaviate | Yes | Excellent |
| Chroma | Yes | Small-Medium |
| pgvector | Yes | PostgreSQL |
| LanceDB | Yes | Local |
| FAISS | Yes | Local |
| Vespa | Yes | Enterprise |

---

# 8. Search Technologies

| Technology | Purpose |
|------------|---------|
| BM25 | Keyword Search |
| Vector Search | Semantic Search |
| Hybrid Search | Combined |
| Re-ranking | Better results |
| Knowledge Graph | Relationships |
| GraphRAG | Graph reasoning |

---

# 9. LLMs

| Model | Local | Best For |
|---------|-------|-----------|
| DeepSeek-R1 | Yes | Reasoning |
| Qwen3 | Yes | Research |
| Llama 3.3 | Yes | General |
| Mistral Large | Yes | Writing |
| Gemma 3 | Yes | Small deployments |
| Phi-4 | Yes | Lightweight |
| Kimi K2 | Yes | Long context |
| GLM-4 | Yes | Large context |

---

# 10. Agent Frameworks

| Framework | Purpose |
|------------|---------|
| CrewAI | Multi-agent research |
| AutoGen | Autonomous agents |
| LangGraph | Stateful agents |
| OpenHands | Coding agents |
| Semantic Kernel | Enterprise orchestration |
| PydanticAI | Python agents |
| SmolAgents | Lightweight agents |
| LLAMA | https://github.com/run-llama/llama_index | 
---

# 11. Browser & Search Integration

| Capability | Open Source Tool |
|-------------|-----------------|
| Google Search | SearXNG |
| Brave Search | API |
| DuckDuckGo | API |
| Bing | API |
| Tavily | API |
| Firecrawl | Website extraction |
| Crawl4AI | Website crawling |
| Playwright | Dynamic websites |
| Browser-use | Browser automation |

---

# 12. Report Generation

| Output | Supported |
|---------|-----------|
| Markdown | Yes |
| HTML | Yes |
| PDF | Yes |
| DOCX | Yes |
| PowerPoint | Yes |
| CSV | Yes |
| Excel | Yes |
| Mermaid Diagrams | Yes |
| Mind Maps | Yes |
| Citations | Yes |

---

# 13. Missing Features Often Forgotten

- Browser history indexing
- Local code repositories
- Git commit history
- Meeting transcripts
- Calendar events
- Voice notes
- Image understanding (Vision LLMs)
- Video summarisation
- Citation verification
- Fact checking
- Source confidence scoring
- Duplicate detection
- Versioned document indexing
- Incremental indexing
- Scheduled refresh
- Metadata tagging
- Knowledge graph creation
- Entity extraction
- Timeline generation
- Automatic summarisation
- Automatic report writing
- Multi-document comparison
- Document change detection
- Prompt templates
- Human review workflow
- Multi-user permissions
- Audit logs
- API access
- MCP (Model Context Protocol) support
- Remote MCP servers
- Local MCP servers
- Tool calling
- Code execution sandbox
- Python notebook execution
- SQL querying
- Workflow automation
- Email notifications
- Webhooks
- Mobile access
- Offline mode
- GPU acceleration
- Multi-GPU inference
- Distributed inference
- Long-term memory
- Conversation memory
- Fine-grained citations
- Inline source attribution
- Semantic caching
- Prompt versioning

---

# 14. Recommended Complete Open Source Stack

| Layer | Recommended Tool |
|---------|------------------|
| Frontend | Open WebUI |
| Agent Framework | LangGraph + CrewAI |
| Workflow Automation | n8n |
| RAG Framework | LlamaIndex |
| OCR | PaddleOCR + OCRmyPDF |
| Document Parsing | Docling + Unstructured |
| Crawling | Crawl4AI + Firecrawl |
| Browser Automation | Playwright |
| Embeddings | BGE-M3 |
| Vector Database | Qdrant |
| Hybrid Search | Qdrant + BM25 |
| Re-ranking | BGE Reranker |
| LLM | DeepSeek-R1 + Qwen3 |
| Vision | Gemma 3 Vision |
| Speech-to-Text | Whisper |
| Report Generation | Pandoc + Markdown |
| Knowledge Graph | GraphRAG |
| Monitoring | OpenTelemetry |
| Containers | Docker Compose or Kubernetes |

---

# Overall Architecture

```
                User
                  │
                  ▼
            Open WebUI
                  │
        ┌─────────┴──────────┐
        ▼                    ▼
    LangGraph            CrewAI Agents
        │                    │
        └─────────┬──────────┘
                  ▼
           Research Orchestrator
                  │
    ┌─────────────┼───────────────────────┐
    ▼             ▼                       ▼
Search      Local Documents         GitHub/Cloud
    │             │                       │
    └─────────────┼───────────────────────┘
                  ▼
        Document Processing Pipeline
                  │
    OCR → Chunking → Embeddings → Qdrant
                  │
                  ▼
            Hybrid Retrieval
                  │
                  ▼
             Re-ranking Layer
                  │
                  ▼
              Reasoning LLM
                  │
                  ▼
      Citation + Verification Layer
                  │
                  ▼
    Markdown • PDF • DOCX • HTML Report
```

This architecture provides an end-to-end, self-hosted deep research capability with document ingestion, semantic search, autonomous agents, reasoning, source citation, and report generation using entirely open-source components.
