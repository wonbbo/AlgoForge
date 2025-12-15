/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  allowedDevOrigins: [
    'http://algoforge.wonbbo.kro.kr',
    'https://algoforge.wonbbo.kro.kr',
    'http://algoforge.wonbbo.kro.kr:80',
    'https://algoforge.wonbbo.kro.kr:443',
    'http://algoforge.wonbbo.kro.kr:5001',
    'https://algoforge.wonbbo.kro.kr:5001',
  ],
  
  // ESLint 설정 (Next.js 14 호환)
  eslint: {
    // 빌드 시 ESLint 검사 수행
    ignoreDuringBuilds: false,
    // 특정 디렉토리만 검사
    dirs: ['app', 'components', 'lib', 'types'],
  },
  
  // FastAPI 백엔드와 통신
  async rewrites() {
    // 배포 환경에서는 환경변수로 백엔드 주소를 주입하고,
    // 기본값은 로컬 개발용 localhost 사용
    const apiBaseUrl = process.env.API_BASE_URL || 'http://localhost:6000'
    return [
      {
        source: '/api/:path*',
        destination: `${apiBaseUrl}/api/:path*`,
      },
    ]
  },
}

module.exports = nextConfig

