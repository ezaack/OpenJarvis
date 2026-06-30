# Configuration Backup

This directory contains external configuration files backed up before a full system format.

> **Warning**: Secrets/credentials are NOT included. Re-authentication is required after restore.

## Contents

### VS Code (`vscode/`)
- `settings.json` — Editor settings, terminal profiles, theme, extensions config
- `concise.instructions.md` — Custom Copilot instructions (concise/silent mode)
- `extensions.txt` — List of installed extensions (reinstall via `code --install-extension <id>`)
- `chatLanguageModels.json` — Chat language model configuration

### OpenJarvis (`openjarvis/`)
- `config.toml` — Agent runtime config (engine, intelligence, tools, digest, speech)
- `SOUL.md` — Agent persona definition
- `MEMORY.md` — Agent memory
- `USER.md` — User profile
- `version-check.json` — Version tracking

### Windows Terminal (`windows-terminal/`)
- `settings.json` — Terminal profiles, keybindings, color schemes
- `wslconfig` — WSL2 config (processor count)

### Git
- `git-config.txt` — Global git configuration (user name/email)

### Agents (`agents/`)
- `skill-lock.json` — Installed agent skills manifest
- `skills/find-skills/SKILL.md` — Find-skills agent skill

### Bin (`bin/`)
- `jarvis.cmd` — CLI entrypoint launcher script

## Restore Notes

1. **Connectors**: OAuth tokens in `~/.openjarvis/connectors/` (gmail, gcalendar, etc.) were **not** backed up (contain secrets). Run `jarvis connect <service>` to re-authenticate.
2. **Databases**: `~/.openjarvis/*.db` files were not backed up (runtime data).
3. **VS Code extensions**: Run `cat vscode/extensions.txt | % { code --install-extension $_ }` to restore.
4. **OpenJarvis**: Copy `openjarvis/*` to `~/.openjarvis/` after installing the agent.
5. **Windows Terminal**: Copy `windows-terminal/settings.json` to `%LOCALAPPDATA%\Packages\Microsoft.WindowsTerminal_8wekyb3d8bbwe\LocalState\settings.json`.
6. **WSL**: Copy `windows-terminal/wslconfig` to `~/.wslconfig`.
