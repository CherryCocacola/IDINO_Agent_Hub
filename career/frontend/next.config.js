/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,

  // Disable webpack caching in development to prevent stale chunks
  webpack: (config, { dev, isServer }) => {
    if (dev && !isServer) {
      // Disable persistent caching in development
      config.cache = false;
    }
    return config;
  },

  // Generate unique build IDs to prevent chunk conflicts
  generateBuildId: async () => {
    return `build-${Date.now()}`;
  },

  // Optimize chunk loading
  experimental: {
    // Enable optimistic client cache
    optimisticClientCache: true,
  },

  async rewrites() {
    const studentHost = process.env.STUDENT_SERVICE_URL || 'http://student-service:8002';
    const competencyHost = process.env.COMPETENCY_SERVICE_URL || 'http://competency-service:8003';
    const alumniHost = process.env.ALUMNI_SERVICE_URL || 'http://alumni-service:8005';
    const integrationHost = process.env.INTEGRATION_SERVICE_URL || 'http://integration-service:8019';
    return [
      {
        source: '/api/students/:path*',
        destination: `${studentHost}/students/:path*`,
      },
      {
        source: '/api/competency/:path*',
        destination: `${competencyHost}/competency/:path*`,
      },
      {
        source: '/api/alumni/:path*',
        destination: `${alumniHost}/alumni/:path*`,
      },
      {
        source: '/api/integration/:path*',
        destination: `${integrationHost}/integration/:path*`,
      },
    ];
  },
};

module.exports = nextConfig;
