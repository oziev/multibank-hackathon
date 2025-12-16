import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useQueries } from '@tanstack/react-query'
import { useGetGroupAccounts } from '@entities/group'
import { Card, CardContent, Skeleton, Button } from '@shared/ui'
import { CreditCard, Building2, ChevronDown, ChevronUp } from 'lucide-react'
import { BANK_NAMES } from '@shared/config'
import { formatCurrency } from '@shared/lib/utils'
import { apiClient, ENDPOINTS } from '@shared/api'
import type { BalanceResponse } from '@shared/api/types'

type GroupAccountsProps = {
  groupId: number
}

export function GroupAccounts({ groupId }: GroupAccountsProps) {
  const navigate = useNavigate()
  const { data: accounts, isLoading } = useGetGroupAccounts(groupId)
  const [showAll, setShowAll] = useState(false)

  const displayedAccounts = showAll ? accounts || [] : (accounts || []).slice(0, 3)
  const hasMore = (accounts || []).length > 3

  const balanceQueries = useQueries({
    queries: displayedAccounts.map((account) => ({
      queryKey: ['balance', account.accountId, parseInt(account.clientId, 10)],
      queryFn: async () => {
        const data = await apiClient.get<BalanceResponse>(
          ENDPOINTS.ACCOUNTS.BALANCES(account.accountId),
          { client_id: parseInt(account.clientId, 10) }
        )
        return data
      },
    })),
  })

  if (isLoading) {
    return (
      <div className="space-y-3">
        <Skeleton className="h-20" />
        <Skeleton className="h-20" />
      </div>
    )
  }

  if (!accounts || accounts.length === 0) {
    return (
      <Card>
        <CardContent className="p-6 text-center">
          <CreditCard className="mx-auto mb-3 h-12 w-12 text-gray-400" />
          <p className="mb-1 text-sm font-medium text-gray-900">Нет счетов</p>
          <p className="text-xs text-gray-500">Участники группы еще не добавили свои счета</p>
        </CardContent>
      </Card>
    )
  }

  return (
    <div className="space-y-3">
      <h3 className="text-lg font-semibold text-gray-900">Счета группы</h3>

      <div className="space-y-2">
        {displayedAccounts.map((account, index) => {
          const clientIdNum = parseInt(account.clientId, 10)
          const borderColor =
            clientIdNum === 1
              ? '#3b82f6'
              : clientIdNum === 2
                ? '#22c55e'
                : clientIdNum === 3
                  ? '#ef4444'
                  : '#d1d5db'

          const balance = balanceQueries[index]?.data

          return (
            <Card
              key={`${groupId}-${account.clientId}`}
              className="cursor-pointer transition-all hover:shadow-md"
              style={{ borderLeft: `6px solid ${borderColor}` }}
              onClick={() =>
                navigate(
                  `/accounts/${account.accountId}?clientId=${clientIdNum}&name=${encodeURIComponent(account.accountName)}`
                )
              }
            >
              <CardContent className="p-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div
                      className="flex h-10 w-10 items-center justify-center rounded-full"
                      style={{ backgroundColor: `${borderColor}20` }}
                    >
                      <Building2 className="h-5 w-5" style={{ color: borderColor }} />
                    </div>
                    <div>
                      <p className="font-medium text-gray-900">{account.accountName}</p>
                      <p className="text-xs text-gray-500">
                        {BANK_NAMES[account.clientId as keyof typeof BANK_NAMES] ||
                          account.clientName}{' '}
                        • {account.owner.name}
                      </p>
                    </div>
                  </div>
                  <div className="text-right">
                    {balance && (
                      <p className="text-sm font-semibold text-gray-900">
                        {formatCurrency(balance.amount, balance.currency)}
                      </p>
                    )}
                  </div>
                </div>
              </CardContent>
            </Card>
          )
        })}
      </div>

      {hasMore && (
        <Button variant="outline" onClick={() => setShowAll(!showAll)} className="w-full">
          {showAll ? (
            <>
              <ChevronUp className="mr-2 h-4 w-4" />
              Скрыть
            </>
          ) : (
            <>
              <ChevronDown className="mr-2 h-4 w-4" />
              Показать все
            </>
          )}
        </Button>
      )}
    </div>
  )
}
