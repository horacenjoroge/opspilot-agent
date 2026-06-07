# Security Notes

- secrets must be loaded from environment variables
- never commit `.env`
- model output is untrusted
- validate all structured model output
- tool names must be allowlisted
- unknown tools must be rejected
- no arbitrary shell execution from model output
- dangerous actions require approval
- the model cannot bypass approval policy
- remediation is simulated in the current implementation
- audit important decisions and actions
- agent step storage redacts sensitive keys in JSON payloads

## Public Demo Safety Notes

- use mock mode by default during ordinary local testing
- use live Qwen only when necessary for final proof
- avoid exposing secrets in screenshots, demos, or logs
- do not present simulated remediation as real infrastructure control
