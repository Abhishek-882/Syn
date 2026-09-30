# Rule: No Fake Silent Skips & Full Operational Transparency

1. **NEVER use `-ErrorAction SilentlyContinue`** in PowerShell or shell commands. All command outputs, exit codes, and errors must remain visible and explicitly handled.
2. **NEVER fake or fabricate live data**: Always maintain strict, honest boundaries between live on-chain data and test fixtures. If an API is rate-limited, unauthorized, or offline, state it clearly.
3. **NEVER silently swallow errors**: Do not use empty `except: pass` or hidden error suppressions. Every exception or warning must be explicitly logged (`logger.warning`, `logger.error`, or terminal output).
4. **Transparent Diagnostics**: When probing ports, services, or endpoints, check and display the actual status rather than suppressing probe outputs.
