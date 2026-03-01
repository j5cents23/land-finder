"use client"

import Link from "next/link"
import { usePathname } from "next/navigation"

const NAV_LINKS = [
  { href: "/", label: "Home" },
  { href: "/listings", label: "Listings" },
  { href: "/saved", label: "Saved" },
  { href: "/criteria", label: "Criteria" },
  { href: "/settings", label: "Settings" },
] as const

export default function Nav() {
  const pathname = usePathname()

  return (
    <nav className="sticky top-0 z-50 border-b border-zinc-200 bg-white/95 backdrop-blur dark:border-zinc-800 dark:bg-zinc-950/95">
      <div className="mx-auto flex h-14 max-w-7xl items-center justify-between px-4">
        <Link href="/" className="text-lg font-bold tracking-tight text-zinc-900 dark:text-zinc-100">
          Land Finder
        </Link>
        <ul className="flex items-center gap-1">
          {NAV_LINKS.map(({ href, label }) => {
            const isActive = href === "/"
              ? pathname === "/"
              : pathname.startsWith(href)

            return (
              <li key={href}>
                <Link
                  href={href}
                  className={`rounded-md px-3 py-2 text-sm font-medium transition-colors ${
                    isActive
                      ? "bg-zinc-100 text-zinc-900 dark:bg-zinc-800 dark:text-zinc-100"
                      : "text-zinc-600 hover:bg-zinc-50 hover:text-zinc-900 dark:text-zinc-400 dark:hover:bg-zinc-800/50 dark:hover:text-zinc-100"
                  }`}
                >
                  {label}
                </Link>
              </li>
            )
          })}
        </ul>
      </div>
    </nav>
  )
}
