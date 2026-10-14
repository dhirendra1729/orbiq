/** @type {import('next').NextConfig} */
const nextConfig = {
    webpack: (config, { isServer }) => {
        if (!isServer) {
            config.resolve.fallback = {
                ...config.resolve.fallback,
                encoding: false,
            };
        }
        return config;
    },
    async rewrites() {
        // On Vercel, serve Next.js serverless route handlers directly
        if (process.env.VERCEL) {
            return [];
        }
        return [
            {
                source: '/api/:path*',
                destination: process.env.BACKEND_URL || 'http://127.0.0.1:8000/api/:path*'
            }
        ];
    }
};

export default nextConfig;
