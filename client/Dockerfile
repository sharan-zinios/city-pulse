# City Pulse Client Dashboard
FROM node:18-alpine

# Set working directory
WORKDIR /app

# Install system dependencies including wget for health checks
RUN apk add --no-cache wget

# Copy package files for dependency installation
COPY package.json package-lock.json ./

# Install dependencies using npm ci for faster, reliable builds
RUN npm ci --only=production

# Copy application code
COPY . .

# Create directory for database files
RUN mkdir -p /app/data

# Expose port
EXPOSE 3002

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
  CMD wget --no-verbose --tries=1 --spider http://localhost:3002/health || exit 1

# Start the application
CMD ["npm", "start"]
