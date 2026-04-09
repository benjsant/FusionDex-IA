import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: "standalone",
  images: {
    remotePatterns: [
      {
        protocol: "http",
        hostname: "localhost",
        port: "8080",
        pathname: "/sprites/**",
      },
      {
        protocol: "http",
        hostname: "fusiondex_sprites",
        port: "80",
        pathname: "/sprites/**",
      },
    ],
  },
};

export default nextConfig;
