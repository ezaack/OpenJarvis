# 1.1 — Install openwakeword + onnxruntime

**Status**: ⬜ | **Deps**: none | **Agent**: any

## Do
1. Add `"openwakeword>=0.6.0"` to the `speech` extra in `src/pyproject.toml`:
   ```
   speech = [
       "faster-whisper>=1.0",
       "openwakeword>=0.6.0",
   ]
   ```
2. Run `uv sync --extra speech`
3. Verify import:
   ```
   uv run python -c "import openwakeword; from openwakeword.model import Model; print('ok')"
   ```

## Done when
`openwakeword` imports without error in project venv. ONNX Runtime (`onnxruntime`) is pulled as a transitive dependency.
