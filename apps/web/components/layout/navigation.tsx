"use client"

import Link from "next/link"
import { usePathname } from "next/navigation"
import { cn } from "@/lib/utils"
import { 
  LayoutDashboard, 
  Database, 
  GitBranch, 
  PlayCircle,
  Gauge
} from "lucide-react"

/**
 * 메인 네비게이션 컴포넌트
 */
export function Navigation() {
  const pathname = usePathname()

  const links = [
    {
      href: "/",
      label: "대시보드",
      icon: LayoutDashboard,
    },
    {
      href: "/datasets",
      label: "데이터셋",
      icon: Database,
    },
    {
      href: "/strategies",
      label: "전략",
      icon: GitBranch,
    },
    {
      href: "/indicators",
      label: "지표",
      icon: Gauge,
    },
    {
      href: "/runs",
      label: "Run",
      icon: PlayCircle,
    },
  ]

  return (
    <nav className="border-b bg-card">
      <div className="container mx-auto px-4 max-w-7xl">
        <div className="flex h-16 items-center justify-between">
          {/* 로고 */}
          <Link href="/" className="flex items-center space-x-2">
            <div className="h-8 w-8 rounded-lg bg-primary flex items-center justify-center">
              <span className="text-primary-foreground font-bold text-lg">A</span>
            </div>
            <span className="font-bold text-xl">AlgoForge</span>
          </Link>

          {/* 네비게이션 링크 */}
          <div className="flex items-center space-x-1">
            {links.map((link) => {
              const Icon = link.icon
              const isActive = pathname === link.href || 
                               (link.href !== "/" && pathname?.startsWith(link.href))

              return (
                <Link
                  key={link.href}
                  href={link.href}
                  className={cn(
                    "flex items-center space-x-2 px-4 py-2 rounded-md text-sm font-medium transition-colors",
                    isActive
                      ? "bg-primary text-primary-foreground"
                      : "text-muted-foreground hover:bg-accent hover:text-accent-foreground"
                  )}
                >
                  <Icon className="h-4 w-4" />
                  <span>{link.label}</span>
                </Link>
              )
            })}
          </div>
        </div>
      </div>
    </nav>
  )
}

