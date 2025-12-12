"use client"

import { useEffect, useState } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Database, GitBranch, PlayCircle, TrendingUp } from "lucide-react"
import Link from "next/link"
import { Button } from "@/components/ui/button"
import { datasetApi, strategyApi, runApi } from "@/lib/api-client"
import type { Dataset, Strategy, Run } from "@/lib/types"

/**
 * 대시보드 페이지
 */
export default function DashboardPage() {
  const [stats, setStats] = useState({
    datasets: 0,
    strategies: 0,
    runs: 0,
    completedRuns: 0,
  })
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    loadStats()
  }, [])

  async function loadStats() {
    try {
      const [datasets, strategies, runs] = await Promise.all([
        datasetApi.list(),
        strategyApi.list(),
        runApi.list(),
      ])

      setStats({
        datasets: datasets.length,
        strategies: strategies.length,
        runs: runs.length,
        completedRuns: runs.filter(r => r.status === 'COMPLETED').length,
      })
    } catch (error) {
      console.error('Failed to load stats:', error)
    } finally {
      setLoading(false)
    }
  }

  const statCards = [
    {
      title: "데이터셋",
      value: stats.datasets,
      icon: Database,
      color: "text-blue-600",
      bgColor: "bg-blue-100",
      href: "/datasets",
    },
    {
      title: "전략",
      value: stats.strategies,
      icon: GitBranch,
      color: "text-green-600",
      bgColor: "bg-green-100",
      href: "/strategies",
    },
    {
      title: "총 Run",
      value: stats.runs,
      icon: PlayCircle,
      color: "text-purple-600",
      bgColor: "bg-purple-100",
      href: "/runs",
    },
    {
      title: "완료된 Run",
      value: stats.completedRuns,
      icon: TrendingUp,
      color: "text-orange-600",
      bgColor: "bg-orange-100",
      href: "/runs",
    },
  ]

  return (
    <div className="space-y-8">
      {/* 헤더 */}
      <div>
        <h1 className="text-3xl font-bold mb-2">대시보드</h1>
        <p className="text-muted-foreground">
          백테스팅 현황을 한눈에 확인하세요
        </p>
      </div>

      {/* 통계 카드 */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {statCards.map((stat) => {
          const Icon = stat.icon
          return (
            <Link key={stat.title} href={stat.href}>
              <Card className="hover:shadow-md transition-shadow cursor-pointer">
                <CardHeader className="flex flex-row items-center justify-between pb-2">
                  <CardTitle className="text-sm font-medium text-muted-foreground">
                    {stat.title}
                  </CardTitle>
                  <div className={cn(stat.bgColor, "p-2 rounded-lg")}>
                    <Icon className={cn(stat.color, "h-4 w-4")} />
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">
                    {loading ? "..." : stat.value}
                  </div>
                </CardContent>
              </Card>
            </Link>
          )
        })}
      </div>

      {/* 빠른 액션 */}
      <Card>
        <CardHeader>
          <CardTitle>빠른 시작</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <Link href="/datasets">
              <Button variant="outline" className="w-full justify-start">
                <Database className="mr-2 h-4 w-4" />
                데이터셋 업로드
              </Button>
            </Link>
            <Link href="/strategies">
              <Button variant="outline" className="w-full justify-start">
                <GitBranch className="mr-2 h-4 w-4" />
                전략 생성
              </Button>
            </Link>
            <Link href="/runs">
              <Button variant="outline" className="w-full justify-start">
                <PlayCircle className="mr-2 h-4 w-4" />
                백테스트 실행
              </Button>
            </Link>
          </div>
        </CardContent>
      </Card>

      {/* 안내 */}
      <Card>
        <CardHeader>
          <CardTitle>시작하기</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3 text-sm">
          <div className="flex items-start space-x-3">
            <div className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-primary text-primary-foreground text-xs font-bold">
              1
            </div>
            <div>
              <p className="font-medium">데이터셋 업로드</p>
              <p className="text-muted-foreground">
                CSV 형식의 봉 데이터를 업로드하세요
              </p>
            </div>
          </div>
          <div className="flex items-start space-x-3">
            <div className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-primary text-primary-foreground text-xs font-bold">
              2
            </div>
            <div>
              <p className="font-medium">전략 생성</p>
              <p className="text-muted-foreground">
                진입/청산 규칙을 정의하여 전략을 만드세요
              </p>
            </div>
          </div>
          <div className="flex items-start space-x-3">
            <div className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-primary text-primary-foreground text-xs font-bold">
              3
            </div>
            <div>
              <p className="font-medium">백테스트 실행</p>
              <p className="text-muted-foreground">
                데이터셋과 전략을 선택하여 Run을 실행하고 결과를 분석하세요
              </p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

function cn(...inputs: any[]) {
  return inputs.filter(Boolean).join(' ')
}

