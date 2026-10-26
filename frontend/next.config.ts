import type { NextConfig } from "next";
const config: NextConfig = {
  async rewrites() {
    return [
      {
        source: "/api/predict",
        destination: `${process.env.API_BASE_URL || "http://127.0.0.1:8000"}/predict`,
      },
    ];
  },
};
export default config;
