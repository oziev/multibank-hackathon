import { useQueries } from '@tanstack/react-query'
import { useGetAccounts } from '@entities/account'
import type { Account } from '@entities/account'
import { Card, CardContent, Skeleton } from '@shared/ui'
import { formatCurrency } from '@shared/lib/utils'
import { Wallet } from 'lucide-react'
import { TransactionsList } from '@widgets/transactions-list'
import { apiClient, ENDPOINTS } from '@shared/api'
import type { BalanceResponse } from '@shared/api/types'

export function DashboardSummary() {
  const { data: accounts, isLoading } = useGetAccounts()

  if (isLoading) {
    return (
      <div className="space-y-6">
        <Card>
          <CardContent className="p-6">
            <Skeleton className="mb-2 h-4 w-32" />
            <Skeleton className="h-10 w-48" />
          </CardContent>
        </Card>
      </div>
    )
  }

  if (!accounts?.length) {
    return null
  }

  return (
    <div className="space-y-6">
      {/* Total Balance Card */}
      <Card className="border-0 bg-gradient-to-r from-purple-600 to-blue-600 text-white shadow-lg">
        <CardContent className="p-6">
          <div className="mb-2 flex items-center gap-2">
            <Wallet className="h-5 w-5" />
            <p className="text-sm font-medium opacity-90">Общий баланс</p>
          </div>
          <TotalBalanceDisplay accounts={accounts} />
        </CardContent>
      </Card>

      {/* Recent Transactions */}
      <div>
        <h3 className="mb-4 text-lg font-semibold text-gray-900">Последние транзакции</h3>
        <TransactionsList />
      </div>
    </div>
  )
}

function TotalBalanceDisplay({ accounts }: { accounts: Account[] }) {
  const balanceQueries = useQueries({
    queries: accounts.map((account) => ({
      queryKey: ['balance', account.accountId, account.clientId],
      queryFn: async () => {
        const data = await apiClient.get<BalanceResponse>(
          ENDPOINTS.ACCOUNTS.BALANCES(account.accountId),
          { client_id: account.clientId }
        )
        return data
      },
    })),
  })

  const total = balanceQueries.reduce((sum, query) => sum + (query.data?.amount || 0), 0)

  return <p className="text-4xl font-bold">{formatCurrency(total, 'RUB')}</p>
}
