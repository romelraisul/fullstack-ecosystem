/** @type {import('next').NextConfig} */
const nextConfig = {
  // Ensure we run a server (API routes work) rather than static export
  // Remove any `output: 'export'` setting.
  output: undefined,
};

module.exports = nextConfig;
/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  swcMinify: true,
}

module.exports = nextConfig
