# Contributing to OmniAgent AI

Thank you for your interest in contributing to **OmniAgent AI**!

## Code of Conduct
We are committed to providing a welcoming, inclusive, and harassment-free experience for everyone.

## Development Workflow
1. Fork the repository and create a descriptive branch: `git checkout -b feature/my-new-feature`
2. Follow architectural boundaries:
   - Keep API routes lightweight. Business logic belongs in `backend/app/services/`.
   - Keep agent logic isolated in `agents/`. Agents communicate with tools via controlled interfaces.
   - Multimodal parsers belong in `multimodal/`.
   - Tool actuators belong in `tools/` with permission and risk definitions.
   - Front-end components follow shadcn/ui and React 18 patterns.
3. Write automated unit and integration tests under `tests/`.
4. Ensure code passes linting and formatting:
   - Python: `ruff check` and `ruff format`
   - TypeScript: `npm run lint` and `npm run build`
5. Submit a Pull Request targeting `main`.

## Commit Style
Follow Conventional Commits:
- `feat:` new feature
- `fix:` bug fix
- `docs:` documentation updates
- `refactor:` code restructuring without feature changes
- `test:` test additions or fixes
- `chore:` maintenance tasks
