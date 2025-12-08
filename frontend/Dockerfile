# MAI Framework V2 - Frontend Dockerfile
# Multi-stage build: Node for building, Nginx for serving

# ============================================
# Stage 1: Build
# ============================================
FROM node:20-alpine AS build

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci

# Copy source code
COPY . .

# Build the application
RUN npm run build

# ============================================
# Stage 2: Production
# ============================================
FROM nginx:stable-alpine AS final

# Create nginx directories for non-root execution
RUN mkdir -p /var/cache/nginx/client_temp \
    && mkdir -p /var/run/nginx \
    && mkdir -p /var/log/nginx \
    && chown -R nginx:nginx /var/cache/nginx \
    && chown -R nginx:nginx /var/run/nginx \
    && chown -R nginx:nginx /var/log/nginx \
    && chown -R nginx:nginx /usr/share/nginx/html \
    && chown -R nginx:nginx /etc/nginx

# Copy custom nginx configuration
COPY --chown=nginx:nginx nginx.conf /etc/nginx/nginx.conf

# Copy built files from build stage
COPY --from=build --chown=nginx:nginx /app/dist /usr/share/nginx/html

# Switch to non-root user
USER nginx

# Expose port 80
EXPOSE 80

# Start Nginx
CMD ["nginx", "-g", "daemon off;"]
