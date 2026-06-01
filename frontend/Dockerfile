# Stage 1: build the Vite app
FROM node:20-alpine AS builder

WORKDIR /app

COPY package*.json ./
# Force IPv4: IPv6 path to npm CDN stalls on this host (connections idle out)
ENV NODE_OPTIONS=--dns-result-order=ipv4first
RUN npm config set fetch-timeout 60000 && npm config set fetch-retries 5
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
