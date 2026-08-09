# Build from monorepo root (see .github/workflows/flowproof-deploy.yml).
FROM node:20-alpine AS builder

WORKDIR /app

RUN apk add --no-cache libc6-compat

COPY package.json yarn.lock ./
COPY products/flowproof/web ./products/flowproof/web

RUN mkdir -p products/flowproof/web/public

RUN yarn install --frozen-lockfile

ENV NEXT_TELEMETRY_DISABLED=1

WORKDIR /app/products/flowproof/web

RUN npx next build

FROM node:20-alpine AS runner

WORKDIR /app

ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1
ENV PORT=3040
ENV HOSTNAME=0.0.0.0

COPY --from=builder /app/products/flowproof/web/.next/standalone ./
COPY --from=builder /app/products/flowproof/web/.next/static ./products/flowproof/web/.next/static
COPY --from=builder /app/products/flowproof/web/public ./products/flowproof/web/public

EXPOSE 3040

CMD ["node", "products/flowproof/web/server.js"]
