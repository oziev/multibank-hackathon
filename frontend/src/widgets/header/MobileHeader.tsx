import { useGetMe } from '@entities/user'
import { LoadingSpinner } from '@shared/ui'

export function MobileHeader() {
  const { data: user, isLoading } = useGetMe()

  return (
    <header className="sticky top-0 z-50 w-full border-b border-gray-200 bg-white shadow-sm">
      <div className="container flex h-14 sm:h-16 items-center justify-between px-3 sm:px-4">
        <div className="min-w-0 flex-1">
          <h1 className="bg-gradient-to-r from-purple-600 to-blue-600 bg-clip-text text-lg sm:text-xl font-bold text-transparent truncate">
            Банк Агрегатор
          </h1>
          {!isLoading && user && <p className="text-xs text-gray-600 truncate">{user.name}</p>}
        </div>
        {isLoading && (
          <div className="flex items-center gap-2">
            <LoadingSpinner size="sm" />
          </div>
        )}
      </div>
    </header>
  )
}
