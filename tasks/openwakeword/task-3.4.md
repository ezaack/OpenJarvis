# 3.4 — End-to-end test: toggle wake word → say "Hey Ada" → transcribe → reply

**Status**: ⬜ | **Deps**: 3.3

## Do
Full end-to-end manual test of the wake word pipeline.

### Test scenario
1. Start the server: `jarvis serve`
2. Open the frontend at `http://localhost:5173`
3. Click the **Wake Word** button (or press `Ctrl+Space` twice — first toggles voice mode, second to enable wake mode)
4. Wait for indicator: `Waiting for "Hey Ada"...`
5. Say **"Hey Ada"** clearly into the mic
6. Verify: indicator changes to `Listening...` (recording started)
7. Speak a query, e.g. **"what's the weather"**
8. Verify: query is transcribed and sent to the model
9. Verify: assistant reply is generated
10. If voice mode auto-continues: verify the loop cycles back to `Waiting for "Hey Ada"...` or `Listening...`

### Edge cases to test
- **Cooldown**: Say "Hey Ada" twice rapidly — second should be ignored for 3s.
- **False positive**: Play non-speech audio (music, background noise) — should not trigger.
- **Silence**: Stay silent — watcher stays active without triggering.
- **Toggle off**: Press `Ctrl+Space` while watching — wake mode disables cleanly.
- **Reconnect**: Stop and restart the server while wake mode is active — frontend should handle WS close gracefully.

## Done when
All test scenarios pass. Wake word is a reliable replacement for the energy-based VAD.
