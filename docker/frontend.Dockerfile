FROM node:22-slim AS base

WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci

EXPOSE 3000

# --- Development: docker-compose.yml bind-mounts source over this. ---
FROM base AS dev
COPY . .
CMD ["npm", "run", "dev"]

# --- Production: builds the app and serves it as a non-root user (the
# official node image already ships a "node" user), no dev server. ---
FROM base AS production
COPY . .
RUN npm run build
USER node
CMD ["npm", "run", "start"]
