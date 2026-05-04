import type { NextConfig } from 'next'

const API_URL = process.env.API_URL || 'http://localhost:8040'

const nextConfig: NextConfig = {
  output: 'standalone',
  serverExternalPackages: [],
  experimental: {
    serverActions: {
      bodySizeLimit: '100mb',
    },
  },
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: `${API_URL}/api/:path*`,
      },
      {
        source: '/ws/:path*',
        destination: `${API_URL}/ws/:path*`,
      },
    ]
  },
}

export default nextConfig
