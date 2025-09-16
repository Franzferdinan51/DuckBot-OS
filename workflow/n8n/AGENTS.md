# Repository Guidelines

## Project Structure & Module Organization
- Source: TypeScript across a multi-package setup under `packages/` (e.g., `packages/cli` for the server, `packages/editor-ui` for the UI, `packages/workflow` and `packages/nodes-*` for shared logic and integrations). Each package has its own `src/` and tests.
- Config & scripts: Root `package.json`, workspace config, linting/formatting, and CI files. Look for `pnpm-workspace.yaml` or lockfiles to determine the package manager.
- Assets & docs: Collocated per package; shared assets may live under `packages/*/assets` or a top-level `docs/`.

## Build, Test, and Development Commands
Use the package manager indicated by the lockfile. Examples below use `pnpm`:
- Install: `pnpm i`
- Build all: `pnpm build`
- Dev server (CLI/backend): `pnpm -F packages/cli dev` or `pnpm start`
- UI dev: `pnpm -F packages/editor-ui dev`
- Test: `pnpm test`
- Lint/format: `pnpm lint` and `pnpm format`
Filter to a single package with `-F <package>` (or `--filter <name>`).

## Coding Style & Naming Conventions
- Language: TypeScript. Prefer 2-space indentation, no semicolons only if enforced by the formatter.
- Style tools: ESLint and Prettier. Run `pnpm lint` and `pnpm format` before commits.
- Naming: `PascalCase` for components/classes, `camelCase` for variables/functions, `SCREAMING_SNAKE_CASE` for constants, and `kebab-case` for file and directory names unless the framework dictates otherwise.

## Testing Guidelines
- Framework: Jest (ts-jest) with tests near code or under `__tests__/`.
- Naming: `*.test.ts` or `*.spec.ts`.
- Running: `pnpm test` or `pnpm -F <package> test`.
- Aim to maintain or improve coverage; write deterministic tests and avoid network calls without mocks.

## Commit & Pull Request Guidelines
- Commits: Follow Conventional Commits (e.g., `feat: add OAuth2 helper`, `fix(editor): correct node validation`). Keep changes focused and messages imperative.
- Branches: `type/short-topic` (e.g., `feat/new-node-slack`).
- PRs: Include a clear description, linked issues (`Closes #123`), test plan, and screenshots/GIFs for UI changes. Ensure `pnpm build`, `pnpm test`, and linters pass.

## Security & Configuration Tips
- Secrets: Use `.env` or platform secrets; never commit credentials. Provide examples in `.env.example`.
- Node/PNPM version: Use the versions in `.nvmrc`/`.node-version` and lockfile; consider `corepack enable`.
- Dependencies: Prefer workspace packages; avoid duplicating versions across packages when possible.

