export default function AuthLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <div className="min-h-screen bg-gradient-to-br from-primary via-secondary to-primary flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        <div className="bg-secondary border border-slate-600 rounded-lg shadow-xl p-8">
          {children}
        </div>
      </div>
    </div>
  )
}
