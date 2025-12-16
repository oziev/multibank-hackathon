# Bank Aggregator - Frontend

React + TypeScript + Vite PWA

## Quick Start

```bash
make help       # Show all commands
make install    # Install deps
make dev        # Dev server
make check      # Run checks
```

## Commands

```bash
make dev            # Start dev server
make build          # Build production
make check          # Typecheck + lint + format
make docker-dev     # Docker dev with hot reload
make docker-build   # Build production image
make up             # Start Docker dev
make down           # Stop Docker dev
```

## Docker

```bash
# Dev with hot reload
make up

# Production
make docker-build
make docker-run
```

## Tech Stack

- React 19 + TypeScript
- Vite + TanStack Query
- Tailwind CSS + Framer Motion
- Feature-Sliced Design (FSD)

## Scripts

- `dev` - Vite dev server
- `build` - Production build
- `check` - Typecheck + lint + format
- `lint` - ESLint
- `format` - Prettier

## License

MIT
