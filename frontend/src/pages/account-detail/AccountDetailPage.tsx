import { useState } from 'react'
import { useParams, useNavigate, useSearchParams } from 'react-router-dom'
import { motion } from 'framer-motion'
import { MobileHeader } from '@widgets/header'
import { BottomNavigation } from '@widgets/bottom-navigation'
import { useGetBalance, useGetTransactions } from '@entities/account'
import { Card, CardContent, Button } from '@shared/ui'
import { ArrowLeft, ArrowUpRight, ArrowDownRight, Clock, ChevronDown } from 'lucide-react'
import { formatCurrency } from '@shared/lib/utils'
import { format } from 'date-fns'
import { ru } from 'date-fns/locale'
import { BANK_NAMES } from '@shared/config'

export function AccountDetailPage() {
  const { id } = useParams<{ id: string }>()
  const [searchParams] = useSearchParams()
  const navigate = useNavigate()
  const clientId = parseInt(searchParams.get('clientId') || '0', 10)
  const accountName = searchParams.get('name') || 'Счёт'

  const [displayCount, setDisplayCount] = useState(20)

  const { data: balance, isLoading: balanceLoading } = useGetBalance(id || '', clientId)
  const { data: transactions, isLoading: transactionsLoading } = useGetTransactions(id || '', { clientId })

  const bankName = BANK_NAMES[clientId as keyof typeof BANK_NAMES] || ''

  const displayedTransactions = transactions?.slice(0, displayCount) || []
  const hasMore = (transactions?.length || 0) > displayCount

  if (!id || !clientId) {
    return (
      <div className="min-h-screen bg-gray-50 pb-20">
        <MobileHeader />
        <main className="container mx-auto px-4 py-6">
          <p className="text-center text-gray-500">Счёт не найден</p>
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
            onClick={() => navigate(-1)}
            className="mb-4 flex items-center gap-2 text-sm text-gray-600 hover:text-gray-900"
          >
            <ArrowLeft className="h-4 w-4" />
            Назад
          </button>

          <h2 className="text-2xl font-bold text-gray-900">{accountName}</h2>
          <p className="text-sm text-gray-500">{bankName}</p>
        </motion.div>

        {/* Balance */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1, duration: 0.5 }}
          className="mb-6"
        >
          <Card className="bg-gradient-to-br from-blue-500 to-cyan-500">
            <CardContent className="p-6">
              <p className="mb-2 text-sm font-medium text-blue-100">Баланс</p>
              {balanceLoading ? (
                <div className="h-9 w-40 animate-pulse rounded bg-white/20" />
              ) : (
                <p className="text-3xl font-bold text-white">
                  {balance ? formatCurrency(balance.amount, balance.currency) : '—'}
                </p>
              )}
            </CardContent>
          </Card>
        </motion.div>

        {/* Transactions */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2, duration: 0.5 }}
          className="space-y-3"
        >
          <h3 className="text-lg font-semibold text-gray-900">Транзакции</h3>

          {transactionsLoading ? (
            <div className="space-y-2">
              {[1, 2, 3].map((i) => (
                <Card key={i}>
                  <CardContent className="p-4">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        <div className="h-10 w-10 animate-pulse rounded-full bg-gray-200" />
                        <div className="space-y-2">
                          <div className="h-4 w-32 animate-pulse rounded bg-gray-200" />
                          <div className="h-3 w-24 animate-pulse rounded bg-gray-200" />
                        </div>
                      </div>
                      <div className="h-5 w-20 animate-pulse rounded bg-gray-200" />
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          ) : !transactions || transactions.length === 0 ? (
            <Card>
              <CardContent className="p-6 text-center">
                <Clock className="mx-auto mb-3 h-12 w-12 text-gray-400" />
                <p className="mb-1 text-sm font-medium text-gray-900">Нет транзакций</p>
                <p className="text-xs text-gray-500">
                  Транзакции появятся после синхронизации с банком
                </p>
              </CardContent>
            </Card>
          ) : (
            <>
              <div className="space-y-2">
                {displayedTransactions.map((transaction) => {
                  const isIncome = transaction.amount > 0
                  const date = new Date(transaction.date)

                  return (
                    <Card key={transaction.id}>
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
