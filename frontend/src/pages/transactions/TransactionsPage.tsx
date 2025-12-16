import { useState } from 'react'
import { motion } from 'framer-motion'
import { MobileHeader } from '@widgets/header'
import { BottomNavigation } from '@widgets/bottom-navigation'
import { useGetAccounts } from '@entities/account/api/accountApi'
import { Card, CardContent, Skeleton, Button } from '@shared/ui'
import { formatCurrency } from '@shared/lib/utils'
import { ArrowUpRight, ArrowDownRight, Clock, X, ArrowLeft } from 'lucide-react'
import { format } from 'date-fns'
import { ru } from 'date-fns/locale'
import { BANK_NAMES } from '@shared/config'
import { apiClient, ENDPOINTS } from '@shared/api'
import type { TransactionResponse } from '@shared/api/types'
import { useQueries, useQuery } from '@tanstack/react-query'
import type { Transaction } from '@entities/transaction'
import type { Account } from '@entities/account'
import { useNavigate } from 'react-router-dom'

type TransactionWithAccount = Transaction & {
  accountId: string
  account: Account
  paymentDetails?: any
}

export function TransactionsPage() {
  const navigate = useNavigate()
  const { data: accounts, isLoading: accountsLoading } = useGetAccounts()

  if (accountsLoading) {
    return (
      <div className="min-h-screen bg-gray-50 pb-20">
        <MobileHeader />
        <div className="space-y-3 p-4">
          <Skeleton className="h-20" />
          <Skeleton className="h-20" />
          <Skeleton className="h-20" />
        </div>
        <BottomNavigation />
      </div>
    )
  }

  if (!accounts?.length) {
    return (
      <div className="min-h-screen bg-gray-50 pb-20">
        <MobileHeader />
        <main className="container mx-auto px-4 py-6">
          <Card>
            <CardContent className="p-6">
              <div className="flex flex-col items-center justify-center py-8 text-center">
                <Clock className="mb-3 h-12 w-12 text-gray-400" />
                <p className="mb-1 text-sm font-medium text-gray-900">Нет счетов</p>
                <p className="text-xs text-gray-500">Подключите банковский счет для просмотра транзакций</p>
              </div>
            </CardContent>
          </Card>
        </main>
        <BottomNavigation />
      </div>
    )
  }

  return <TransactionsContent accounts={accounts} navigate={navigate} />
}

function TransactionsContent({ accounts, navigate }: { accounts: Account[], navigate: (path: string) => void }) {
  const [selectedTransaction, setSelectedTransaction] = useState<TransactionWithAccount | null>(null)

  // Получаем транзакции из Bank API
  const transactionQueries = useQueries({
    queries: accounts.map((account) => ({
      queryKey: ['transactions', account.accountId, account.clientId],
      queryFn: async () => {
        try {
          const data = await apiClient.get<TransactionResponse[]>(
            ENDPOINTS.ACCOUNTS.TRANSACTIONS(account.accountId),
            { client_id: account.clientId }
          )
          return data.map((tx) => ({
            id: tx.id,
            date: tx.date,
            description: tx.description,
            amount: tx.amount,
            currency: tx.currency,
            type: tx.type,
          }))
        } catch (error) {
          console.error(`Ошибка получения транзакций для ${account.accountId}:`, error)
          return []
        }
      },
      refetchInterval: 5000,
    })),
  })

  // Получаем внутренние платежи
  const { data: paymentsData } = useQuery({
    queryKey: ['payments', 'history'],
    queryFn: async () => {
      try {
        const response = await apiClient.get<any[]>('/api/payments/history?limit=200')
        return Array.isArray(response) ? response : []
      } catch (error) {
        console.error('Ошибка получения истории платежей:', error)
        return []
      }
    },
    refetchInterval: 3000,
  })

  // Объединяем транзакции из Bank API
  const bankTransactions: TransactionWithAccount[] = transactionQueries
    .flatMap((query, index) =>
      (query.data || []).map((transaction: Transaction) => ({
        ...transaction,
        account: accounts[index],
      }))
    )

  // Преобразуем внутренние платежи в формат транзакций
  const internalTransactions: TransactionWithAccount[] = (paymentsData || [])
    .filter((payment: any) => payment && payment.id)
    .map((payment: any) => {
      const isIncoming = payment.isIncoming || false
      let account
      if (isIncoming) {
        account = accounts[0]
      } else {
        account = accounts.find(acc => acc.accountName === payment.fromAccountName) || accounts[0]
      }
      
      if (!account) return null
      
      let description = payment.description
      if (!description) {
        if (payment.paymentType === 'TO_PERSON') {
          if (isIncoming) {
            description = `Перевод от ${payment.fromUserId ? 'пользователя' : payment.fromAccountName || ''}`
          } else {
            description = `Перевод ${payment.toName || payment.toPhone || ''}`
          }
        } else if (payment.paymentType === 'PREMIUM') {
          description = 'Оплата Premium подписки'
        } else {
          description = 'Платеж'
        }
      }
      
      return {
        id: `payment_${payment.id}`,
        date: payment.completedAt || payment.createdAt,
        description: description,
        amount: isIncoming ? payment.amount : -payment.amount,
        currency: payment.currency || 'RUB',
        type: isIncoming ? 'credit' : 'debit',
        account: account,
        paymentDetails: payment,
      }
    })
    .filter((tx: any) => tx !== null)

  // Объединяем все транзакции и сортируем по дате
  const allTransactions: TransactionWithAccount[] = [
    ...bankTransactions,
    ...internalTransactions
  ]
    .sort((a, b) => new Date(b.date).getTime() - new Date(a.date).getTime())

  if (!allTransactions.length) {
    return (
      <div className="min-h-screen bg-gray-50 pb-20">
        <MobileHeader />
        <main className="container mx-auto px-4 py-6">
          <button
            onClick={() => navigate(-1)}
            className="mb-4 flex items-center gap-2 text-sm text-gray-600 hover:text-gray-900"
          >
            <ArrowLeft className="h-4 w-4" />
            Назад
          </button>
          <Card>
            <CardContent className="p-6">
              <div className="flex flex-col items-center justify-center py-8 text-center">
                <Clock className="mb-3 h-12 w-12 text-gray-400" />
                <p className="mb-1 text-sm font-medium text-gray-900">Пока нет транзакций</p>
                <p className="text-xs text-gray-500">
                  Транзакции появятся после синхронизации с банками
                </p>
              </div>
            </CardContent>
          </Card>
        </main>
        <BottomNavigation />
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50 pb-20">
      <MobileHeader />
      <main className="container mx-auto px-4 py-6">
        <button
          onClick={() => navigate(-1)}
          className="mb-4 flex items-center gap-2 text-sm text-gray-600 hover:text-gray-900"
        >
          <ArrowLeft className="h-4 w-4" />
          Назад
        </button>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-6"
        >
          <h2 className="mb-2 text-2xl font-bold text-gray-900">Все транзакции</h2>
          <p className="text-gray-600">История всех операций по счетам</p>
        </motion.div>

        <div className="space-y-3">
          {allTransactions.map((transaction, index) => (
            <TransactionItem
              key={`all-${transaction.account.accountId}-${transaction.id}-${index}`}
              transaction={transaction}
              onClick={() => setSelectedTransaction(transaction)}
            />
          ))}
        </div>
      </main>

      {selectedTransaction && (
        <TransactionDetailsModal
          transaction={selectedTransaction}
          onClose={() => setSelectedTransaction(null)}
        />
      )}

      <BottomNavigation />
    </div>
  )
}

function TransactionItem({
  transaction,
  onClick,
}: {
  transaction: TransactionWithAccount
  onClick: () => void
}) {
  const isIncome = transaction.amount > 0
  const date = new Date(transaction.date)
  const bankName =
    BANK_NAMES[transaction.account.clientId as keyof typeof BANK_NAMES] ||
    transaction.account.clientName

  return (
    <Card className="cursor-pointer transition-all hover:shadow-md" onClick={onClick}>
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
                {transaction.account.accountName} • {bankName}
              </p>
            </div>
          </div>
          <div className="text-right">
            <p className={`text-lg font-semibold ${isIncome ? 'text-green-600' : 'text-red-600'}`}>
              {isIncome && '+'}
              {formatCurrency(Math.abs(transaction.amount), transaction.currency)}
            </p>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}

function TransactionDetailsModal({
  transaction,
  onClose,
}: {
  transaction: TransactionWithAccount
  onClose: () => void
}) {
  const isIncome = transaction.amount > 0
  const date = new Date(transaction.date)
  const bankName =
    BANK_NAMES[transaction.account.clientId as keyof typeof BANK_NAMES] ||
    transaction.account.clientName
  const isInternalPayment = transaction.id.startsWith('payment_')
  const paymentDetails = transaction.paymentDetails

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4" onClick={onClose}>
      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        className="w-full max-w-md rounded-2xl bg-white p-6 shadow-xl"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="mb-4 flex items-center justify-between">
          <h3 className="text-xl font-bold text-gray-900">Детали транзакции</h3>
          <button onClick={onClose} className="rounded-full p-1 hover:bg-gray-100">
            <X className="h-5 w-5" />
          </button>
        </div>

        <div className="space-y-4">
          <div>
            <p className="text-sm text-gray-500">Описание</p>
            <p className="text-lg font-medium text-gray-900">{transaction.description}</p>
          </div>

          <div>
            <p className="text-sm text-gray-500">Сумма</p>
            <p className={`text-2xl font-bold ${isIncome ? 'text-green-600' : 'text-red-600'}`}>
              {isIncome && '+'}
              {formatCurrency(Math.abs(transaction.amount), transaction.currency)}
            </p>
          </div>

          <div>
            <p className="text-sm text-gray-500">Дата и время</p>
            <p className="text-base text-gray-900">
              {format(date, 'd MMMM yyyy, HH:mm', { locale: ru })}
            </p>
          </div>

          {isInternalPayment && paymentDetails ? (
            <>
              <div className="border-t pt-4">
                <p className="mb-2 text-sm font-semibold text-gray-700">Информация о счетах</p>
                <div className="space-y-2">
                  <div>
                    <p className="text-xs text-gray-500">Счет списания</p>
                    <p className="text-sm font-medium text-gray-900">
                      {paymentDetails.fromAccountName || 'Не указан'}
                    </p>
                  </div>
                  {paymentDetails.isIncoming && (
                    <div>
                      <p className="text-xs text-gray-500">Счет получения</p>
                      <p className="text-sm font-medium text-gray-900">
                        {transaction.account.accountName} • {bankName}
                      </p>
                    </div>
                  )}
                  {!paymentDetails.isIncoming && paymentDetails.toName && (
                    <div>
                      <p className="text-xs text-gray-500">Получатель</p>
                      <p className="text-sm font-medium text-gray-900">
                        {paymentDetails.toName}
                        {paymentDetails.toPhone && ` (${paymentDetails.toPhone})`}
                      </p>
                    </div>
                  )}
                </div>
              </div>
            </>
          ) : (
            <div className="border-t pt-4">
              <p className="mb-2 text-sm font-semibold text-gray-700">Счет</p>
              <p className="text-sm text-gray-900">
                {transaction.account.accountName} • {bankName}
              </p>
            </div>
          )}

          <Button onClick={onClose} className="w-full">
            Закрыть
          </Button>
        </div>
      </motion.div>
    </div>
  )
}

