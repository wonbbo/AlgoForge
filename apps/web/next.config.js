/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  
  // ESLint 설정 (Next.js 14 호환)
  eslint: {
    // 빌드 시 ESLint 검사 수행
    ignoreDuringBuilds: false,
    // 특정 디렉토리만 검사
    dirs: ['app', 'components', 'lib', 'types'],
  },
  
  // FastAPI 백엔드와 통신
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: 'http://localhost:8000/api/:path*',
      },
    ]
  },
}

module.exports = nextConfig

