# Frontend Dockerfile - Multi-stage build for React + Vite
# Stage 1: Builder - Build the React app
FROM node:20-alpine as builder

WORKDIR /app

# Copy package files and all source code
COPY . .

# Install dependencies
RUN npm ci

# Build the application
RUN npm run build


# Stage 2: Runtime - Serve with Nginx
FROM nginx:alpine

# Copy nginx configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copy built app from builder
COPY --from=builder /app/dist /usr/share/nginx/html

# Nginx user typically already exists in Alpine, just ensure correct permissions
RUN chown -R nginx:nginx /usr/share/nginx/html

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD wget --quiet --tries=1 --spider http://localhost:80/ || exit 1

# Expose port
EXPOSE 80

# Start nginx
CMD ["nginx", "-g", "daemon off;"]
