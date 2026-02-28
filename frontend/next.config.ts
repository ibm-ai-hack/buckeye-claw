import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  async rewrites() {
    return [
      { source: "/api/:path*", destination: "http://localhost:5001/api/:path*" },
      { source: "/auth/:path*", destination: "http://localhost:5001/auth/:path*" },
    ];
  },
};

export default nextConfig;
