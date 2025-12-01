/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  swcMinify: true,
  // Ensure we run a server (API routes work) rather than static export
  output: undefined,
};

module.exports = nextConfig;