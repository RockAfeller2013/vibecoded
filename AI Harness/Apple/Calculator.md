# Apple MLX LLM Cluster Cost Calculator

- https://gemini.google.com/app/b55263f0c68bdb04?hl=en-AU
- https://www.apple.com/au/shop/buy-mac/mac-studio?
- https://chatgpt.com/c/6addc567-1610-83ec-b190-047fe23afa6b


Build a complete, single-file `index.html` frontend-only calculator using HTML5, CSS3, Bootstrap 5, and vanilla JavaScript.

## Objective

Calculate the minimum number of Apple MacBook Pros with 256 GB unified memory required to run a selected large language model (LLM) using Apple MLX, and display the total hardware cost in AUD.

### 1. Inputs

**Model selection**
- Searchable catalogue of MLX/MLX-LM-compatible models.
- Include verified models from Qwen, Llama, DeepSeek, Mistral, Gemma, GPT-OSS, and other supported families.
- Store model name, version, parameter count, architecture, layer count, attention configuration, context window, licence, and source URL.
- Distinguish dense models from mixture-of-experts (MoE) models.
- For MoE, distinguish total parameters from active parameters.

**Quantisation**
- Offer only available, model-specific MLX quantisation variants.
- Support 2-bit, 3-bit, 4-bit, 6-bit, 8-bit, FP16, and BF16 where verified.
- Display the selected format, bits per weight, and actual model-file size when known.
- Estimate weight storage using model-specific metadata, quantisation scales, and other overhead.

**Inference requirements**
- Context length.
- Maximum generation length.
- Concurrent requests.
- Batch size, where supported.
- KV cache precision and quantisation, where supported.
- Multimodal components, where applicable.
- Model-specific runtime requirements.

Update available settings when the selected model changes.

### 2. Hardware configuration

Use a configurable local hardware catalogue containing:

- MacBook Pro model and generation.
- Apple Silicon chip.
- Unified memory.
- SSD capacity.
- Australian price in AUD.
- Source URL and last-verified date.

The target is 256 GB unified memory per MacBook Pro. Verify that the selected Apple configuration actually exists. If unavailable, display a clear warning and permit an explicitly labelled hypothetical configuration.

### 3. Memory calculation

Calculate:

- Quantised model weights.
- Quantisation metadata and scales.
- KV cache.
- Runtime and temporary buffers.
- Multimodal components.
- macOS and background-process reserve.
- Configurable safety margin.
- Total estimated inference memory.
- Estimated usable memory per machine.

Use architecture-specific calculations where metadata permits. Do not estimate MoE memory from active parameters alone.

Distinguish model-file storage from inference memory.

### 4. Apple MLX compatibility

Target Apple MLX and MLX-LM exclusively.

Maintain compatibility data for each model, including supported quantisation, context length, model architecture, and distributed inference support.

Distinguish between:

1. Running a complete model independently on one Mac.
2. Distributing model weights across multiple Macs.
3. Supported pipeline-parallel execution.
4. Experimental or unsupported distributed execution.

Do not assume that multiple Macs automatically pool unified memory.

If a model exceeds the available memory of one Mac, recommend multiple machines only when a verified MLX-compatible distributed execution method supports that model. Otherwise, report that the configuration is unsupported or unverified.

### 5. Required outputs

Display prominently:

- **Minimum number of MacBook Pros required.**
- **Total purchase cost in AUD.**
- Price per MacBook.
- Total unified memory.
- Total SSD capacity.
- Selected model and quantisation.
- Context length and concurrency.
- Estimated model-weight memory.
- Estimated total inference memory.
- Estimated memory allocation per machine.
- Estimated SSD requirement per machine.
- Required inference method.
- Compatibility status and limitations.

Use these statuses:

- Supported — estimated to fit.
- Supported — distributed inference required.
- Experimental — compatibility not fully verified.
- Unsupported — no validated deployment path.
- Insufficient data — requirements cannot be calculated reliably.

Do not calculate a definitive minimum cluster size for unsupported configurations.

### 6. Quantisation comparison

Generate a comparison table dynamically for supported variants.

| Quantisation | Model memory | Required Macs | Total cost (AUD) | Compatibility |
|---|---:|---:|---:|---|
| 4-bit | Calculated | Calculated | Calculated | Verified status |
| 6-bit | Calculated | Calculated | Calculated | Verified status |
| 8-bit | Calculated | Calculated | Calculated | Verified status |
| 16-bit | Calculated | Calculated | Calculated | Verified status |

Allow comparisons across context lengths and concurrency settings.

### 7. Cost calculation

Calculate:

`Total cost = number of MacBooks × unit price in AUD`

Allow manual price overrides. Identify manually entered prices and distinguish them from verified Apple prices.

Exclude accessories and networking unless explicitly configured.

### 8. User interface

Include:

- Responsive Bootstrap 5 dashboard.
- Model and quantisation selectors.
- Context and concurrency controls.
- KV cache settings.
- Hardware and pricing summary.
- Minimum cluster size and total cost.
- Per-machine memory breakdown.
- Quantisation comparison table.
- Compatibility warnings.
- Source links.
- Dark and light themes.
- JSON and CSV export.
- Reset-to-default control.
- Immediate recalculation without page reloads.

### 9. Technical requirements

- Deliver the complete, runnable `index.html`.
- Use vanilla JavaScript.
- Keep the UI, hardware catalogue, model metadata, calculations, pricing, and compatibility data in this single file.
- No backend, database, API keys, subscriptions, or build process.
- The calculator must work locally in a browser.
- Do not download model weights automatically.
- Include source URLs and last-verified dates.
- Clearly distinguish verified data, estimates, and hypothetical configurations.
- Do not fabricate Apple pricing, model support, memory requirements, or performance benchmarks.

### Expected result

The user selects an MLX-compatible LLM, chooses a supported quantisation, configures context length and other inference requirements, and immediately sees the estimated minimum number of 256 GB MacBook Pros required and their total purchase cost in AUD.

Prioritise technically defensible estimates and verified MLX compatibility over optimistic cluster-size calculations.
