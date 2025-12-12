const nextJest = require('next/jest')

const createJestConfig = nextJest({
  // next.config.js 및 .env 파일을 로드할 Next.js 앱의 경로
  dir: './',
})

// Jest에 전달할 커스텀 설정
const customJestConfig = {
  // 각 테스트 실행 전에 추가 설정 옵션
  setupFilesAfterEnv: ['<rootDir>/jest.setup.js'],
  
  // 모듈 경로 매핑 (tsconfig.json paths와 동일하게)
  moduleNameMapper: {
    '^@/(.*)$': '<rootDir>/$1',
  },
  
  // 테스트 환경
  testEnvironment: 'jest-environment-jsdom',
  
  // 테스트 파일 패턴
  testMatch: [
    '**/__tests__/**/*.test.ts',
    '**/__tests__/**/*.test.tsx',
  ],
  
  // 커버리지 제외 경로
  collectCoverageFrom: [
    'lib/**/*.{ts,tsx}',
    'app/**/*.{ts,tsx}',
    '!**/*.d.ts',
    '!**/node_modules/**',
    '!**/.next/**',
  ],
}

// createJestConfig는 비동기이므로 export
module.exports = createJestConfig(customJestConfig)

