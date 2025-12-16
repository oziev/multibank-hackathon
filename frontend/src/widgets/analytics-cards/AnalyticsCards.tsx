import { useState } from 'react'
import { Card, CardContent, Skeleton } from '@shared/ui'
import { useGetAnalyticsOverview } from '@entities/analytics'
import { formatCurrency } from '@shared/lib/utils'
import { Wallet, TrendingDown, TrendingUp, PieChart as PieChartIcon, Eye, EyeOff } from 'lucide-react'

export function AnalyticsCards() {
  const { data: analytics, isLoading, error } = useGetAnalyticsOverview()
  const [isBalanceVisible, setIsBalanceVisible] = useState(true)

  // Если нет авторизации - не показываем карточки
  if (error) {
    return null
  }

  if (isLoading) {
    return (
      <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
        <Skeleton className="h-32" />
        <Skeleton className="h-32" />
        <Skeleton className="h-32" />
      </div>
    )
  }

  if (!analytics) {
    return null
  }

  const expenseChange = analytics.currentMonth.expenseChange
  const incomeChange = analytics.currentMonth.incomeChange

  return (
    <div className="space-y-4">
      {/* Общий баланс */}
      <Card className="border-0 bg-gradient-to-r from-purple-600 to-blue-600 text-white shadow-lg">
        <CardContent className="p-6">
          <div className="flex items-center justify-between">
            <div className="flex-1">
              <div className="mb-2 flex items-center gap-2">
                <Wallet className="h-5 w-5 opacity-90" />
                <p className="text-sm font-medium opacity-90">Общий баланс</p>
              </div>
              <p className="text-4xl font-bold">
                {isBalanceVisible ? formatCurrency(analytics.totalBalance, 'RUB') : '•••••• ₽'}
              </p>
              {analytics.accountsCount > 0 && (
                <p className="mt-2 text-sm opacity-75">
                  {analytics.accountsCount} {analytics.accountsCount === 1 ? 'счет' : 'счетов'}
                </p>
              )}
            </div>
            <button
              onClick={() => setIsBalanceVisible(!isBalanceVisible)}
              className="rounded-full bg-white/20 p-3 transition-all hover:bg-white/30 active:scale-95"
            >
              {isBalanceVisible ? (
                <Eye className="h-6 w-6" />
              ) : (
                <EyeOff className="h-6 w-6" />
              )}
            </button>
          </div>
        </CardContent>
      </Card>

      {/* Расходы и доходы */}
      <div className="grid grid-cols-2 gap-4">
        {/* Расходы */}
        <Card>
          <CardContent className="p-4">
            <div className="mb-2 flex items-center gap-2 text-red-600">
              <TrendingDown className="h-4 w-4" />
              <p className="text-xs font-medium">Расходы</p>
            </div>
            <p className="text-xl font-bold text-gray-900">
              {formatCurrency(analytics.currentMonth.expenses, 'RUB')}
            </p>
            {expenseChange !== 0 && (
              <div className={`mt-1 flex items-center gap-1 text-xs ${expenseChange > 0 ? 'text-red-600' : 'text-green-600'}`}>
                {expenseChange > 0 ? '+' : ''}
                {expenseChange.toFixed(1)}%
                <span className="text-gray-500">к прошлому месяцу</span>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Доходы */}
        <Card>
          <CardContent className="p-4">
            <div className="mb-2 flex items-center gap-2 text-green-600">
              <TrendingUp className="h-4 w-4" />
              <p className="text-xs font-medium">Доходы</p>
            </div>
            <p className="text-xl font-bold text-gray-900">
              {formatCurrency(analytics.currentMonth.income, 'RUB')}
            </p>
            {incomeChange !== 0 && (
              <div className={`mt-1 flex items-center gap-1 text-xs ${incomeChange > 0 ? 'text-green-600' : 'text-red-600'}`}>
                {incomeChange > 0 ? '+' : ''}
                {incomeChange.toFixed(1)}%
                <span className="text-gray-500">к прошлому месяцу</span>
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Топ категории */}
      {analytics.topCategories && analytics.topCategories.length > 0 && (
        <Card>
          <CardContent className="p-4">
            <div className="mb-3 flex items-center gap-2">
              <PieChartIcon className="h-4 w-4 text-purple-600" />
              <h3 className="text-sm font-semibold">Топ категории расходов</h3>
            </div>
            <div className="space-y-2">
              {analytics.topCategories.slice(0, 5).map((cat) => (
                <div key={cat.category} className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span className="text-lg">{getCategoryIcon(cat.category)}</span>
                    <span className="text-sm text-gray-700">{cat.categoryName}</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-medium">
                      {formatCurrency(cat.amount, 'RUB')}
                    </span>
                    <span className="text-xs text-gray-500">
                      {cat.percentage.toFixed(0)}%
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  )
}

function getCategoryIcon(category: string): string {
  const icons: Record<string, string> = {
    groceries: '🛒',
    restaurants: '🍽️',
    transport: '🚗',
    clothing: '👔',
    health: '💊',
    entertainment: '🎮',
    travel: '✈️',
    sports: '🏃',
    beauty: '💄',
    utilities: '📞',
    education: '🎓',
    children: '👶',
    home: '🏠',
    transfers: '💸',
    other: '📋',
  }
  return icons[category] || '📋'
}
