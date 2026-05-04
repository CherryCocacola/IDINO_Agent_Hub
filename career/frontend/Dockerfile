FROM node:20-alpine

WORKDIR /app

# Install libc compatibility for SWC
RUN apk add --no-cache libc6-compat

# Install dependencies (NODE_OPTIONS needed for OpenSSL 3 compatibility on Alpine)
COPY frontend/package*.json ./
ENV NODE_OPTIONS=--openssl-legacy-provider
RUN npm ci --legacy-peer-deps
RUN npm install @next/swc-linux-x64-musl --legacy-peer-deps || echo "musl SWC install failed, will use WASM fallback"
ENV NODE_OPTIONS=

# Disable runtime SWC download attempts
ENV NEXT_SWC_DOWNLOAD=false

# Copy application code
COPY frontend/ .

# Expose port
EXPOSE 3000

# Run the development server
CMD ["npm", "run", "dev"]
