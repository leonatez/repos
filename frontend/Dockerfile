# Stage 1: build the Vite app
FROM node:20-alpine AS builder

WORKDIR /app

COPY package*.json ./
# Resilient install: low concurrency + timeouts (flaky path to npm CDN)
RUN npm config set maxsockets 1 \
 && npm config set fetch-retries 6 \
 && npm config set fetch-retry-mintimeout 20000 \
 && npm config set fetch-retry-maxtimeout 120000 \
 && npm config set fetch-timeout 600000
RUN npm ci --no-audit --no-fund

COPY . .

# Injected at build time by CapRover build arguments
ARG VITE_API_URL
ARG VITE_SUPABASE_URL
ARG VITE_SUPABASE_ANON_KEY

ENV VITE_API_URL=$VITE_API_URL
ENV VITE_SUPABASE_URL=$VITE_SUPABASE_URL
ENV VITE_SUPABASE_ANON_KEY=$VITE_SUPABASE_ANON_KEY

RUN npm run build

# Stage 2: serve with nginx on port 1112
FROM nginx:alpine

COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 1112

CMD ["nginx", "-g", "daemon off;"]
