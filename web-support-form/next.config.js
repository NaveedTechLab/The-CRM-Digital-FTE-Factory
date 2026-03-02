/** @type {import('next').NextConfig} */
const nextConfig = {
  async rewrites() {
    return [
      {
        source: '/support/:path*',
        destination: 'http://localhost:8002/support/:path*',
      },
      {
        source: '/api/:path*',
        destination: 'http://localhost:8002/api/:path*',
      },
    ];
  },
};

module.exports = nextConfig;
