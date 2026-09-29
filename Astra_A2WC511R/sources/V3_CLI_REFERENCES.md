# v3 runtime references — checked 2026-09-25

These are external vendor documentation, distinct from the Dev.zip-derived audit. Installed CLI/model metadata remains the runtime authority. The preserved original MerpMod source revision is not upgraded merely because another website is newer.

- OpenAI Codex app-server protocol and model catalog: https://learn.chatgpt.com/docs/app-server — initialization, model/list and advertised supportedReasoningEfforts; account/client-specific availability. Preflight uses metadata only, not thread/start or turn/start.
- OpenAI developer CLI commands: https://learn.chatgpt.com/docs/developer-commands?surface=cli — working directory, sandbox/approval flags, web search, exec/stdin/JSON output, explicit session resume.
- OpenAI configuration reference: https://learn.chatgpt.com/docs/config-file/config-reference — actual accepted configuration fields; effort must be supported by the chosen model.
- OpenAI Work and Codex: https://help.openai.com/en/articles/20001275-chatgpt-work-and-codex — Astra requires CLI 0.153.0 or newer; account and workspace access matter.
- OpenAI usage guidance: https://help.openai.com/en/articles/20001516-managing-usage-with-gpt-6-astra-in-work-and-codex — large context, reasoning effort and Fast can increase usage; higher effort does not supply missing access or evidence. A long-run request is not unlimited allowance.
- OpenAI Windows support: https://learn.chatgpt.com/docs/windows/windows-sandbox — Windows 10 best-effort status; verify the actual LTSC host rather than assuming compatibility.
- Official Codex source/installation: https://github.com/openai/codex — native Windows install path, https://chatgpt.com/codex/install.ps1. Review vendor scripts and preserve existing tools.
- Official Hex-Rays MCP: https://github.com/HexRaysSA/ida-mcp — IDA9.4+ / idalib prerequisites and vendor GUI integration. Use the local vendor schema, preserve one writer to the IDB, and do not run a competing custom IDA server.

No online model catalog check was made against the user's signed-in Codex account during archive preparation. tools/codex_model_probe.py performs that check locally before the main task, without asking the model to generate work.
