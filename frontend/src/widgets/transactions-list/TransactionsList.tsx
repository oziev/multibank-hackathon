import { useState } from 'react'
import { motion } from 'framer-motion'
import { useQueries, useQuery } from '@tanstack/react-query'
import { useGetAccounts } from '@entities/account/api/accountApi'
import type { Transaction } from '@entities/transaction'
import type { Account } from '@entities/account'
import { Card, CardContent, Skeleton, Button } from '@shared/ui'
import { formatCurrency } from '@shared/lib/utils'
import { ArrowUpRight, ArrowDownRight, Clock, X } from 'lucide-react'
import { format } from 'date-fns'
import { ru } from 'date-fns/locale'
import { BANK_NAMES } from '@shared/config'
import { apiClient, ENDPOINTS } from '@shared/api'
import type { TransactionResponse } from '@shared/api/types'

type TransactionWithAccount = Transaction & {
  accountId: string
  account: Account
}

export function TransactionsList() {
  const { data: accounts, isLoading: accountsLoading } = useGetAccounts()

  if (accountsLoading) {
    return (
      <div className="space-y-3">
        <Skeleton className="h-20" />
        <Skeleton className="h-20" />
        <Skeleton className="h-20" />
      </div>
    )
  }

  if (!accounts?.length) {
    return null
  }

  return <TransactionsContent accounts={accounts} />
}

function TransactionsContent({ accounts }: { accounts: Account[] }) {
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
      refetchInterval: 5000, // Обновляем каждые 5 секунд
    })),
  })

  // Получаем внутренние платежи из нашей системы
  const { data: paymentsData } = useQuery({
    queryKey: ['payments', 'history'],
    queryFn: async () => {
      try {
        // apiClient.get уже возвращает data из { success: true, data: [...] }
        const response = await apiClient.get<any[]>('/api/payments/history?limit=50')
        // response уже является массивом платежей
        return Array.isArray(response) ? response : []
      } catch (error) {
        console.error('Ошибка получения истории платежей:', error)
        return []
      }
    },
    refetchInterval: 3000, // Обновляем каждые 3 секунды
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
    .filter((payment: any) => payment && payment.id) // Фильтруем пустые записи
    .map((payment: any) => {
      // Определяем, входящий это платеж или исходящий
      const isIncoming = payment.isIncoming || false
      
      // Для входящих платежей находим счет получателя, для исходящих - отправителя
      let account
      if (isIncoming) {
        // Для входящих платежей используем первый доступный счет (или можно найти по toUserId)
        account = accounts[0]
      } else {
        // Для исходящих платежей находим счет по from_account_name
        account = accounts.find(acc => acc.accountName === payment.fromAccountName) || accounts[0]
      }
      
      if (!account) {
        return null
      }
      
      // Определяем тип платежа для описания
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
        amount: isIncoming ? payment.amount : -payment.amount, // Положительное для входящих, отрицательное для исходящих
        currency: payment.currency || 'RUB',
        type: isIncoming ? 'credit' : 'debit',
        account: account,
      }
    })
    .filter((tx: any) => tx !== null) // Убираем null значения

  // Объединяем все транзакции и сортируем по дате
  const allTransactions: TransactionWithAccount[] = [
    ...bankTransactions,
    ...internalTransactions
  ]
    .sort((a, b) => new Date(b.date).getTime() - new Date(a.date).getTime())
    .slice(0, 5)

  if (!allTransactions.length) {
    return (
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
    )
  }

  return (
    <div className="space-y-3">
      {allTransactions.map((transaction, index) => (
        <TransactionItem
          key={`dashboard-${transaction.account.accountId}-${transaction.id}-${index}`}
          transaction={transaction}
        />
      ))}
    </div>
  )
}

function TransactionItem({ transaction }: { transaction: TransactionWithAccount }) {
  const [showDetails, setShowDetails] = useState(false)
  const isIncome = transaction.amount > 0
  const date = new Date(transaction.date)
  const bankName =
    BANK_NAMES[transaction.account.clientId as keyof typeof BANK_NAMES] ||
    transaction.account.clientName

  // Извлекаем информацию о счетах из ID транзакции (для внутренних платежей)
  const isInternalPayment = transaction.id.startsWith('payment_')
  const paymentId = isInternalPayment ? transaction.id.replace('payment_', '') : null

  return (
    <>
      <Card className="cursor-pointer transition-all hover:shadow-md" onClick={() => setShowDetails(true)}>
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

      {/* Модальное окно деталей транзакции */}
      {showDetails && (
        <TransactionDetailsModal
          transaction={transaction}
          isInternalPayment={isInternalPayment}
          paymentId={paymentId}
          onClose={() => setShowDetails(false)}
        />
      )}
    </>
  )
}

function TransactionDetailsModal({
  transaction,
  isInternalPayment,
  paymentId,
  onClose,
}: {
  transaction: TransactionWithAccount
  isInternalPayment: boolean
  paymentId: string | null
  onClose: () => void
}) {
  const { data: paymentDetails } = useQuery({
    queryKey: ['payment', paymentId],
    queryFn: async () => {
      if (!paymentId) return null
      const response = await apiClient.get(`/api/payments/history?limit=100`)
      return Array.isArray(response) ? response.find((p: any) => p.id === parseInt(paymentId)) : null
    },
    enabled: !!paymentId && isInternalPayment,
  })

  const isIncome = transaction.amount > 0
  const date = new Date(transaction.date)
  const bankName =
    BANK_NAMES[transaction.account.clientId as keyof typeof BANK_NAMES] ||
    transaction.account.clientName

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
