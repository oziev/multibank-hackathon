import { useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import { useQueries } from '@tanstack/react-query'
import { MobileHeader } from '@widgets/header'
import { BottomNavigation } from '@widgets/bottom-navigation'
import { useGetGroups, useGetGroupAccounts } from '@entities/group'
import type { Transaction, GroupAccount } from '@entities/account'
import { Card, CardContent, Button } from '@shared/ui'
import { ArrowLeft, ArrowUpRight, ArrowDownRight, Clock, ChevronDown } from 'lucide-react'
import { formatCurrency } from '@shared/lib/utils'
import { format } from 'date-fns'
import { ru } from 'date-fns/locale'
import { BANK_NAMES } from '@shared/config'
import { apiClient, ENDPOINTS } from '@shared/api'
import type { TransactionResponse } from '@shared/api/types'

type TransactionWithAccount = Transaction & {
  accountId: string
  account: GroupAccount
}

export function GroupTransactionsPage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const groupId = parseInt(id || '0', 10)

  const [displayCount, setDisplayCount] = useState(20)

  const { data: groups } = useGetGroups()
  const { data: accounts } = useGetGroupAccounts(groupId)

  const group = groups?.find((g) => g.id === groupId)

  const transactionQueries = useQueries({
    queries: (accounts || []).map((account) => ({
      queryKey: ['transactions', account.accountId, parseInt(account.clientId, 10)],
      queryFn: async () => {
        const data = await apiClient.get<TransactionResponse[]>(
          ENDPOINTS.ACCOUNTS.TRANSACTIONS(account.accountId),
          { client_id: parseInt(account.clientId, 10) }
        )
        return data.map((tx) => ({
          id: tx.id,
          date: tx.date,
          description: tx.description,
          amount: tx.amount,
          currency: tx.currency,
          type: tx.type,
        }))
      },
    })),
  })

  const allTransactions: TransactionWithAccount[] = transactionQueries
    .flatMap((query, index) =>
      (query.data || []).map((transaction: Transaction) => ({
        ...transaction,
        account: accounts![index],
      }))
    )
    .sort((a, b) => new Date(b.date).getTime() - new Date(a.date).getTime())

  const displayedTransactions = allTransactions.slice(0, displayCount)
  const hasMore = allTransactions.length > displayCount

  if (!group) {
    return (
      <div className="min-h-screen bg-gray-50 pb-20">
        <MobileHeader />
        <main className="container mx-auto px-4 py-6">
          <p className="text-center text-gray-500">Группа не найдена</p>
        </main>
        <BottomNavigation />
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50 pb-20">
      <MobileHeader />

      <main className="container mx-auto px-4 py-6">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
          className="mb-6"
        >
          <button
            onClick={() => navigate(`/groups/${groupId}`)}
            className="mb-4 flex items-center gap-2 text-sm text-gray-600 hover:text-gray-900"
          >
            <ArrowLeft className="h-4 w-4" />
            Назад к группе
          </button>

          <h2 className="text-2xl font-bold text-gray-900">Все транзакции</h2>
          <p className="text-sm text-gray-500">{group.name}</p>
        </motion.div>

        {/* Transactions */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1, duration: 0.5 }}
          className="space-y-3"
        >
          {!allTransactions.length ? (
            <Card>
              <CardContent className="p-6 text-center">
                <Clock className="mx-auto mb-3 h-12 w-12 text-gray-400" />
                <p className="mb-1 text-sm font-medium text-gray-900">Пока нет транзакций</p>
                <p className="text-xs text-gray-500">
                  Транзакции появятся после синхронизации с банками
                </p>
              </CardContent>
            </Card>
          ) : (
            <>
              <div className="space-y-2">
                {displayedTransactions.map((transaction) => {
                  const isIncome = transaction.amount > 0
                  const date = new Date(transaction.date)
                  const clientIdNum = parseInt(transaction.account.clientId, 10)
                  const bankName =
                    BANK_NAMES[clientIdNum as keyof typeof BANK_NAMES] ||
                    transaction.account.clientName

                  return (
                    <Card key={`${groupId}-${transaction.account.accountId}-${transaction.id}`}>
                      <CardContent className="p-4">
                        <div className="flex items-center justify-between">
                          <div className="flex items-center gap-3">
                            <div
                              className={`flex h-10 w-10 items-center justify-center rounded-full ${
                                isIncome ? 'bg-green-100' : 'bg-red-100'
                              }`}
                            >
                              {isIncome ? (
                                <ArrowDownRight className="h-5 w-5 text-green-600" />
                              ) : (
                                <ArrowUpRight className="h-5 w-5 text-red-600" />
                              )}
                            </div>
                            <div>
                              <p className="font-medium text-gray-900">{transaction.description}</p>
                              <p className="text-xs text-gray-500">
                                {format(date, 'd MMMM yyyy, HH:mm', { locale: ru })}
                              </p>
                              <p className="text-xs text-gray-500">
                                {transaction.account.accountName} • {bankName} •{' '}
                                {transaction.account.owner.name}
                              </p>
                            </div>
                          </div>
                          <div className="text-right">
                            <p
                              className={`text-lg font-semibold ${isIncome ? 'text-green-600' : 'text-red-600'}`}
                            >
                              {isIncome && '+'}
                              {formatCurrency(Math.abs(transaction.amount), transaction.currency)}
                            </p>
                          </div>
                        </div>
                      </CardContent>
                    </Card>
                  )
                })}
              </div>

              {hasMore && (
                <Button
                  variant="outline"
                  onClick={() => setDisplayCount(displayCount + 20)}
                  className="w-full"
                >
                  <ChevronDown className="mr-2 h-4 w-4" />
                  Показать ещё
                </Button>
              )}
            </>
          )}
        </motion.div>
      </main>

      <BottomNavigation />
    </div>
  )
}
