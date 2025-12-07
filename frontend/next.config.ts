import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  /* config options here */
  images: {
    unoptimized: true,
  },
  // Enable standalone output for Docker
  output: 'standalone',
};

export default nextConfig;
