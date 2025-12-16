FROM node:20-alpine AS base
RUN corepack enable && corepack prepare pnpm@latest --activate
WORKDIR /app
COPY package.json pnpm-lock.yaml ./

FROM base AS dependencies
RUN pnpm install --frozen-lockfile

FROM base AS development
COPY --from=dependencies /app/node_modules ./node_modules
COPY . .
EXPOSE 5173
CMD ["pnpm", "run", "dev", "--host", "0.0.0.0"]

FROM dependencies AS builder
COPY . .
RUN pnpm run build

FROM nginx:alpine AS production
RUN apk add --no-cache curl
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=builder /app/dist /usr/share/nginx/html
HEALTHCHECK --interval=30s --timeout=3s CMD curl -f http://localhost/health || exit 1
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
