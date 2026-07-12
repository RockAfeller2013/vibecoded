# Apple AI



# Apple Clustering and MLX

# Apple Core AI

- https://developer.apple.com/documentation/coreai
- Core AI Models - https://github.com/apple/coreai-models
- Build intelligent experiences - https://developer.apple.com/machine-learning/
- Apple Intelligence and machine learning - https://developer.apple.com/documentation/TechnologyOverviews/ai-machine-learning
- Meet Core AI WWDC26 - https://developer.apple.com/videos/play/wwdc2026/324/


# Apple Foundation Models (AFM) Cloud - https://machinelearning.apple.com/research/introducing-third-generation-of-apple-foundation-models

# Apple Hardware and NPU Comparision

## M5 Comparision 

| Feature                           |            Apple M5 |        Apple M5 Pro |        Apple M5 Max |
| --------------------------------- | ------------------: | ------------------: | ------------------: |
| **Manufacturing Process**         |     TSMC 3 nm (N3P) |     TSMC 3 nm (N3P) |     TSMC 3 nm (N3P) |
| **CPU Architecture**              | ARMv9 Apple Silicon | ARMv9 Apple Silicon | ARMv9 Apple Silicon |
| **Performance Cores (P-Cores)**   |                   6 |               10–12 |                  12 |
| **Efficiency Cores (E-Cores)**    |                   4 |                 5–6 |                   6 |
| **Total CPU Cores**               |                  10 |               15–18 |                  18 |
| **GPU Cores**                     |                8–10 |               16–20 |               32–40 |
| **Hardware Ray Tracing**          |                 Yes |                 Yes |                 Yes |
| **Dynamic Caching**               |                 Yes |                 Yes |                 Yes |
| **Mesh Shading**                  |                 Yes |                 Yes |                 Yes |
| **Neural Engine (NPU)**           |             16-core |             16-core |             16-core |
| **Neural Engine Performance**     |      Up to ~38 TOPS |      Up to ~38 TOPS |      Up to ~38 TOPS |
| **Media Engine**                  |                 Yes |            Enhanced |     Enhanced (Dual) |
| **Hardware H.264 Encode**         |                 Yes |                 Yes |                 Yes |
| **Hardware H.264 Decode**         |                 Yes |                 Yes |                 Yes |
| **Hardware HEVC Encode**          |                 Yes |                 Yes |                 Yes |
| **Hardware HEVC Decode**          |                 Yes |                 Yes |                 Yes |
| **ProRes Encode**                 |                 Yes |                 Yes |                 Yes |
| **ProRes Decode**                 |                 Yes |                 Yes |                 Yes |
| **AV1 Decode**                    |                 Yes |                 Yes |                 Yes |
| **AV1 Encode**                    |                  No |                  No |                  No |
| **Video Encode Engines**          |                   1 |                   1 |                   2 |
| **Video Decode Engines**          |                   1 |                   1 |                   2 |
| **ProRes Engines**                |                   1 |                   1 |                   2 |
| **Display Engine**                |                 Yes |            Enhanced |            Enhanced |
| **Unified Memory Architecture**   |                 Yes |                 Yes |                 Yes |
| **Memory Bandwidth**              |            120 GB/s |            273 GB/s |            546 GB/s |
| **Maximum Unified Memory**        |               32 GB |               64 GB |              128 GB |
| **Secure Enclave**                |                 Yes |                 Yes |                 Yes |
| **Hardware AES Engine**           |                 Yes |                 Yes |                 Yes |
| **Memory Compression**            |                 Yes |                 Yes |                 Yes |
| **Virtualization Support**        |                 Yes |                 Yes |                 Yes |
| **Thunderbolt Controller**        |       Thunderbolt 5 |       Thunderbolt 5 |       Thunderbolt 5 |
| **Neural Engine API**             |             Core ML |             Core ML |             Core ML |
| **Machine Learning Accelerators** |     CPU + GPU + NPU |     CPU + GPU + NPU |     CPU + GPU + NPU |

## M5 Comparision 

| Processor  |         CPU |         GPU |                NPU | Memory Bandwidth | Max Memory |   Media Engines |
| ---------- | ----------: | ----------: | -----------------: | ---------------: | ---------: | --------------: |
| **M5**     |    10 cores |  8–10 cores | 16-core (~38 TOPS) |         120 GB/s |      32 GB |          Single |
| **M5 Pro** | 15–18 cores | 16–20 cores | 16-core (~38 TOPS) |         273 GB/s |      64 GB | Enhanced Single |
| **M5 Max** |    18 cores | 32–40 cores | 16-core (~38 TOPS) |         546 GB/s |     128 GB |            Dual |

## Mini Comparision

| Feature                           |      Mac mini (M5) |          Mac mini (M5 Pro) |
| --------------------------------- | -----------------: | -------------------------: |
| **Manufacturing Process**         |     TSMC 3nm (N3P) |             TSMC 3nm (N3P) |
| **CPU**                           |  10-core (6P + 4E) | 15–18-core (10–12P + 5–6E) |
| **GPU**                           |          8–10-core |                 16–20-core |
| **Neural Engine (NPU)**           | 16-core (~38 TOPS) |         16-core (~38 TOPS) |
| **Machine Learning Accelerators** |    CPU + GPU + NPU |            CPU + GPU + NPU |
| **Hardware Ray Tracing**          |                Yes |                        Yes |
| **Dynamic Caching**               |                Yes |                        Yes |
| **Mesh Shading**                  |                Yes |                        Yes |
| **Unified Memory**                |        Up to 32 GB |                Up to 64 GB |
| **Memory Bandwidth**              |           120 GB/s |                   273 GB/s |
| **Media Engine**                  |             Single |                   Enhanced |
| **Video Encode Engines**          |                  1 |                          1 |
| **Video Decode Engines**          |                  1 |                          1 |
| **ProRes Encode/Decode Engines**  |                  1 |                          1 |
| **AV1 Decode**                    |                Yes |                        Yes |
| **AV1 Encode**                    |                 No |                         No |
| **Thunderbolt**                   |      Thunderbolt 5 |              Thunderbolt 5 |
| **Display Engine**                |                Yes |                   Enhanced |
| **Secure Enclave**                |                Yes |                        Yes |
| **Hardware AES Engine**           |                Yes |                        Yes |
| **Virtualization Support**        |                Yes |                        Yes |


| Feature                           |       Mac Studio (M4 Max) |     Mac Studio (M3 Ultra) |
| --------------------------------- | ------------------------: | ------------------------: |
| **Manufacturing Process**         |                  TSMC 3nm |                  TSMC 3nm |
| **CPU**                           | 14–16 cores (10–12P + 4E) | 28–32 cores (20–24P + 8E) |
| **GPU**                           |               32–40 cores |               60–80 cores |
| **Neural Engine (NPU)**           |                   16-core |                   32-core |
| **Machine Learning Accelerators** |           CPU + GPU + NPU |           CPU + GPU + NPU |
| **Hardware Ray Tracing**          |                       Yes |                       Yes |
| **Dynamic Caching**               |                       Yes |                       Yes |
| **Mesh Shading**                  |                       Yes |                       Yes |
| **Unified Memory**                |                 36–128 GB |                96–512 GB* |
| **Memory Bandwidth**              |              410–546 GB/s |                  819 GB/s |
| **Media Engine**                  |                  Enhanced |                     Ultra |
| **Video Encode Engines**          |                         2 |                         4 |
| **Video Decode Engines**          |                         1 |                         2 |
| **ProRes Encode/Decode Engines**  |                         2 |                         4 |
| **AV1 Decode**                    |                       Yes |                       Yes |
| **AV1 Encode**                    |                        No |                        No |
| **Thunderbolt**                   |             Thunderbolt 5 |             Thunderbolt 5 |
| **Display Engine**                |                  Enhanced |                     Ultra |
| **Secure Enclave**                |                       Yes |                       Yes |
| **Hardware AES Engine**           |                       Yes |                       Yes |
| **Virtualization Support**        |                       Yes |                       Yes |


| Model                     |   CPU |   GPU |                NPU | Memory Bandwidth | Max Memory | Media Engines |
| ------------------------- | ----: | ----: | -----------------: | ---------------: | ---------: | ------------: |
| **Mac mini (M5)**         |    10 |  8–10 | 16-core (~38 TOPS) |         120 GB/s |      32 GB |        Single |
| **Mac mini (M5 Pro)**     | 15–18 | 16–20 | 16-core (~38 TOPS) |         273 GB/s |      64 GB |      Enhanced |
| **Mac Studio (M4 Max)**   | 14–16 | 32–40 |            16-core |     410–546 GB/s |     128 GB |   Dual Encode |
| **Mac Studio (M3 Ultra)** | 28–32 | 60–80 |            32-core |         819 GB/s |     512 GB |   Quad Encode |
