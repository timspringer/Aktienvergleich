import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'Aktienvergleich - Stock Index Data Comparison',
  description: 'Compare stock valuation estimates across global indexes',
  charset: 'utf-8',
  viewport: 'width=device-width, initial-scale=1',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body className="bg-primary text-white">
        <header className="border-b border-secondary bg-secondary px-6 py-4">
          <div className="max-w-7xl mx-auto">
            <h1 className="text-3xl font-bold text-accent">Aktienvergleich</h1>
            <p className="text-sm text-gray-400 mt-1">
              Global Stock Index Data Comparison Platform
            </p>
          </div>
        </header>
        <main className="min-h-screen">
          <div className="max-w-7xl mx-auto p-6">{children}</div>
        </main>
        <footer className="border-t border-secondary bg-secondary px-6 py-4 mt-12">
          <div className="max-w-7xl mx-auto text-center text-sm text-gray-400">
            <p>Aktienvergleich © 2024 | Stock data sourced from multiple providers</p>
          </div>
        </footer>
      </body>
    </html>
  )
}
