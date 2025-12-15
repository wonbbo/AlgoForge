import { defineConfig, devices } from '@playwright/test';

/**
 * Playwright E2E 테스트 설정
 * 
 * 전략 빌더 UI의 전체 플로우를 브라우저에서 테스트
 */
export default defineConfig({
  // 테스트 디렉토리
  testDir: './e2e',
  
  // 전체 테스트 타임아웃 (30초)
  timeout: 30 * 1000,
  
  // expect 타임아웃 (5초)
  expect: {
    timeout: 5000
  },
  
  // 테스트 실행 설정
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  
  // 리포터
  reporter: 'html',
  
  // 모든 테스트에 공통 적용
  use: {
    // 베이스 URL
    baseURL: 'http://localhost:5001',
    
    // 스크린샷 (실패 시에만)
    screenshot: 'only-on-failure',
    
    // 비디오 (실패 시에만)
    video: 'retain-on-failure',
    
    // 트레이스 (실패 시에만)
    trace: 'on-first-retry',
  },
  
  // 브라우저 설정
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
    
    // Firefox, Safari는 선택적
    // {
    //   name: 'firefox',
    //   use: { ...devices['Desktop Firefox'] },
    // },
  ],
  
  // 개발 서버 (테스트 전 자동 실행)
  webServer: {
    command: 'pnpm dev',
    url: 'http://localhost:5001',
    reuseExistingServer: !process.env.CI,
    timeout: 120 * 1000,
  },
});

