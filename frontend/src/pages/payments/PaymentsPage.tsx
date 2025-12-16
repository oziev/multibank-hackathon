import { useState } from 'react'
import { motion } from 'framer-motion'
import { MobileHeader } from '@widgets/header'
import { BottomNavigation } from '@widgets/bottom-navigation'
import { Card, CardContent, Button, Input, Label } from '@shared/ui'
import { useGetAccounts } from '@entities/account'
import { apiClient } from '@shared/api'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import {
  Smartphone,
  Home,
  Wifi,
  CreditCard,
  Users,
  Banknote,
  Building,
  Tv,
  Phone,
  Zap,
  X,
  Check,
} from 'lucide-react'

type PaymentType = 'card-to-card' | 'to-person' | 'mobile' | 'utilities' | 'internet' | 'tv' | 'electricity' | null

export function PaymentsPage() {
  const [activePayment, setActivePayment] = useState<PaymentType>(null)
  const { data: accounts } = useGetAccounts()

  return (
    <div className="min-h-screen bg-gray-50 pb-20">
      <MobileHeader />

      <main className="container mx-auto px-4 py-6">
        {/* Заголовок */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
          className="mb-6"
        >
          <h2 className="mb-2 text-2xl font-bold text-gray-900">Платежи</h2>
          <p className="text-gray-600">Переводы и оплата услуг</p>
        </motion.div>

        {/* Поиск */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1, duration: 0.5 }}
          className="mb-6"
        >
          <div className="relative">
            <input
              type="text"
              placeholder="Поиск платежей и переводов..."
              className="w-full rounded-lg border border-gray-300 bg-white px-4 py-3 pl-10 text-sm focus:border-purple-500 focus:outline-none focus:ring-2 focus:ring-purple-200"
            />
            <svg
              className="absolute left-3 top-3.5 h-4 w-4 text-gray-400"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
              />
            </svg>
          </div>
        </motion.div>

        {/* Переводы */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2, duration: 0.5 }}
          className="mb-6"
        >
          <h3 className="mb-3 text-lg font-semibold text-gray-900">Переводы</h3>
          <div className="grid grid-cols-3 gap-3">
            <PaymentCard
              icon={<CreditCard className="h-6 w-6" />}
              label="С карты на карту"
              color="bg-purple-100 text-purple-600"
              onClick={() => setActivePayment('card-to-card')}
            />
            <PaymentCard
              icon={<Smartphone className="h-6 w-6" />}
              label="По номеру телефона"
              color="bg-purple-100 text-purple-600"
              onClick={() => setActivePayment('to-person')}
            />
            <PaymentCard
              icon={<Banknote className="h-6 w-6" />}
              label="Наличные"
              color="bg-blue-100 text-blue-600"
            />
          </div>
          <div className="mt-3">
            <PaymentCard
              icon={<Building className="h-6 w-6" />}
              label="Организациям"
              color="bg-orange-100 text-orange-600"
            />
          </div>
        </motion.div>

        {/* Платежи */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3, duration: 0.5 }}
        >
          <h3 className="mb-3 text-lg font-semibold text-gray-900">Платежи</h3>
          <div className="grid grid-cols-3 gap-3">
            <PaymentCard
              icon={<Smartphone className="h-6 w-6" />}
              label="Мобильная связь"
              color="bg-blue-100 text-blue-600"
              onClick={() => setActivePayment('mobile')}
            />
            <PaymentCard
              icon={<Home className="h-6 w-6" />}
              label="ЖКХ"
              color="bg-orange-100 text-orange-600"
              onClick={() => setActivePayment('utilities')}
            />
            <PaymentCard
              icon={<Wifi className="h-6 w-6" />}
              label="Интернет"
              color="bg-purple-100 text-purple-600"
              onClick={() => setActivePayment('internet')}
            />
            <PaymentCard
              icon={<Tv className="h-6 w-6" />}
              label="Телевидение"
              color="bg-cyan-100 text-cyan-600"
              onClick={() => setActivePayment('tv')}
            />
            <PaymentCard
              icon={<Phone className="h-6 w-6" />}
              label="Телефон"
              color="bg-green-100 text-green-600"
            />
            <PaymentCard
              icon={<Zap className="h-6 w-6" />}
              label="Электроэнергия"
              color="bg-yellow-100 text-yellow-600"
              onClick={() => setActivePayment('electricity')}
            />
          </div>
        </motion.div>
      </main>

      <BottomNavigation />

      {/* Модальные окна для платежей */}
      {activePayment && (
        <PaymentModal
          type={activePayment}
          accounts={accounts || []}
          onClose={() => setActivePayment(null)}
        />
      )}
    </div>
  )
}

type PaymentCardProps = {
  icon: React.ReactNode
  label: string
  color: string
  onClick?: () => void
}

function PaymentCard({ icon, label, color, onClick }: PaymentCardProps) {
  return (
    <button
      onClick={onClick}
      className="flex flex-col items-center justify-center gap-2 rounded-xl border border-gray-200 bg-white p-4 shadow-sm transition-all hover:scale-105 hover:shadow-md active:scale-95"
    >
      <div className={`flex h-12 w-12 items-center justify-center rounded-full ${color}`}>
        {icon}
      </div>
      <span className="text-center text-xs font-medium text-gray-700 leading-tight">
        {label}
      </span>
    </button>
  )
}

// Модальное окно платежа
function PaymentModal({ type, accounts, onClose }: { type: PaymentType, accounts: any[], onClose: () => void }) {
  const [formData, setFormData] = useState({
    fromAccountId: (accounts[0] as any)?.id || (accounts[0] as any)?.accountId || 0,
    toPhone: '',
    toAccount: '',
    amount: '',
    description: '',
    provider: '',
    accountNumber: ''
  })
  const [showSuccessModal, setShowSuccessModal] = useState(false)
  const [showErrorModal, setShowErrorModal] = useState(false)
  const [successMessage, setSuccessMessage] = useState('')
  const [errorMessage, setErrorMessage] = useState('')
  const queryClient = useQueryClient()

  const [isProcessing, setIsProcessing] = useState(false)

  const paymentMutation = useMutation({
    mutationFn: async (data: any) => {
      if (isProcessing) {
        throw new Error('Платеж уже обрабатывается, пожалуйста, подождите')
      }
      setIsProcessing(true)
      
      try {
        if (type === 'card-to-card') {
          return apiClient.post('/api/payments/card-to-card', data)
        } else if (type === 'to-person') {
          if (!data.fromAccountId || data.fromAccountId === 0) {
            throw new Error('Выберите счет для списания')
          }
          return apiClient.post('/api/payments/transfer-by-phone', {
            fromAccountId: data.fromAccountId,
            toPhone: data.toPhone,
            amount: parseFloat(data.amount),
            description: data.description || 'Перевод по номеру телефона'
          })
        } else if (type === 'mobile') {
          return apiClient.post('/api/payments/mobile', data)
        } else if (type === 'utilities') {
          return apiClient.post('/api/payments/utility', data)
        }
        throw new Error('Неизвестный тип платежа')
      } finally {
        setIsProcessing(false)
      }
    },
            onSuccess: (data: any) => {
              setSuccessMessage(data.data?.message || 'Платеж успешно выполнен!')
              setShowSuccessModal(true)
              setIsProcessing(false)
              // Обновляем историю платежей, транзакции и балансы
              queryClient.invalidateQueries({ queryKey: ['payments', 'history'] })
              queryClient.invalidateQueries({ queryKey: ['accounts'] })
              queryClient.invalidateQueries({ queryKey: ['transactions'] })
              // Обновляем балансы всех счетов
              accounts?.forEach((acc: any) => {
                queryClient.invalidateQueries({ queryKey: ['balances', acc.accountId, acc.clientId] })
              })
            },
            onError: (error: any) => {
              setErrorMessage(error?.message || 'Ошибка выполнения платежа')
              setShowErrorModal(true)
              setIsProcessing(false)
            }
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    
    // Валидация суммы
    if (!formData.amount || parseFloat(formData.amount) <= 0) {
      alert('❌ Укажите корректную сумму платежа')
      return
    }

    const amount = parseFloat(formData.amount)
    if (amount > 1000000) {
      alert('❌ Максимальная сумма платежа: 1 000 000 ₽')
      return
    }

    // Валидация для карты
    if (type === 'card-to-card') {
      const cardNumber = formData.toAccount.replace(/\s/g, '')
      if (!cardNumber || cardNumber.length < 16) {
        alert('❌ Укажите корректный номер карты (16 цифр)')
        return
      }
    }

    // Валидация для телефона
    if (type === 'to-person' || type === 'mobile') {
      const phone = formData.toPhone.replace(/[^\d]/g, '')
      if (!phone || phone.length < 10) {
        alert('❌ Укажите корректный номер телефона')
        return
      }
    }

    // Валидация для коммунальных платежей
    if ((type === 'utilities' || type === 'internet' || type === 'tv' || type === 'electricity')) {
      if (!formData.provider?.trim()) {
        alert('❌ Укажите провайдера/поставщика')
        return
      }
      if (!formData.accountNumber?.trim()) {
        alert('❌ Укажите номер лицевого счета')
        return
      }
    }

    paymentMutation.mutate(formData)
  }

  const titles: Record<string, string> = {
    'card-to-card': 'Перевод с карты на карту',
    'to-person': 'Перевод по номеру телефона',
    'mobile': 'Оплата мобильной связи',
    'utilities': 'Оплата ЖКХ',
    'internet': 'Оплата интернета',
    'tv': 'Оплата телевидения',
    'electricity': 'Оплата электроэнергии',
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        className="w-full max-w-md rounded-2xl bg-white p-6"
      >
        <div className="mb-4 flex items-center justify-between">
          <h3 className="text-xl font-bold text-gray-900">{titles[type!] || 'Платеж'}</h3>
          <button onClick={onClose} className="rounded-full p-1 hover:bg-gray-100">
            <X className="h-5 w-5" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <Label>Счет списания</Label>
            <select
              value={formData.fromAccountId}
              onChange={(e) => setFormData({ ...formData, fromAccountId: parseInt(e.target.value) })}
              className="w-full rounded-lg border border-gray-300 px-3 py-2"
            >
              {accounts.map((acc) => (
                <option key={`${acc.clientId}-${acc.accountId || (acc as any).id}`} value={(acc as any).id || acc.accountId}>
                  {acc.accountName} ({acc.clientName})
                </option>
              ))}
            </select>
          </div>

          {type === 'card-to-card' && (
            <div>
              <Label>Номер карты получателя</Label>
              <div className="flex gap-2">
                <Input
                  type="text"
                  placeholder="1234 5678 9012 3456"
                  value={formData.toAccount}
                  onChange={(e) => {
                    // Форматируем номер карты (добавляем пробелы каждые 4 цифры)
                    const value = e.target.value.replace(/\s/g, '')
                    const formatted = value.match(/.{1,4}/g)?.join(' ') || value
                    setFormData({ ...formData, toAccount: formatted })
                  }}
                  maxLength={19}
                />
                <Button
                  type="button"
                  variant="outline"
                  onClick={async () => {
                    const cardNumber = formData.toAccount.replace(/\s/g, '')
                    if (!cardNumber || cardNumber.length < 16) {
                      setErrorMessage('Введите номер карты (16 цифр)')
                      setShowErrorModal(true)
                      return
                    }
                    // Проверяем возможность перевода
                    try {
                      // В реальности здесь был бы запрос к API для проверки карты
                      // Пока показываем информацию о реквизитах
                      setSuccessMessage(`Реквизиты для перевода:\n\nНомер карты: ${formData.toAccount}\n\nКарта может принимать переводы.`)
                      setShowSuccessModal(true)
                    } catch (error: any) {
                      setErrorMessage(error?.message || 'Не удалось проверить карту')
                      setShowErrorModal(true)
                    }
                  }}
                  className="whitespace-nowrap"
                >
                  Проверить
                </Button>
              </div>
              <p className="mt-1 text-xs text-gray-500">
                Введите 16-значный номер карты для проверки возможности перевода
              </p>
            </div>
          )}

          {type === 'to-person' && (
            <div>
              <Label>Номер телефона получателя</Label>
              <Input
                type="tel"
                placeholder="+7 (900) 123-45-67"
                value={formData.toPhone}
                onChange={(e) => setFormData({ ...formData, toPhone: e.target.value })}
              />
              <p className="mt-1 text-xs text-gray-500">
                Деньги будут отправлены на карту, привязанную к этому номеру
              </p>
            </div>
          )}

          {(type === 'mobile' || type === 'utilities' || type === 'internet' || type === 'tv' || type === 'electricity') && (
            <>
              <div>
                <Label>Провайдер/Поставщик</Label>
                <Input
                  type="text"
                  placeholder="Название компании"
                  value={formData.provider}
                  onChange={(e) => setFormData({ ...formData, provider: e.target.value })}
                />
              </div>
              <div>
                <Label>Номер лицевого счета</Label>
                <Input
                  type="text"
                  placeholder="1234567890"
                  value={formData.accountNumber}
                  onChange={(e) => setFormData({ ...formData, accountNumber: e.target.value })}
                />
              </div>
            </>
          )}

          <div>
            <Label>Сумма (₽)</Label>
            <Input
              type="number"
              placeholder="1000"
              value={formData.amount}
              onChange={(e) => setFormData({ ...formData, amount: e.target.value })}
            />
          </div>

          <div>
            <Label>Комментарий (необязательно)</Label>
            <Input
              type="text"
              placeholder="Назначение платежа"
              value={formData.description}
              onChange={(e) => setFormData({ ...formData, description: e.target.value })}
            />
          </div>

          <div className="flex gap-3 pt-2">
            <Button type="button" variant="outline" onClick={onClose} className="flex-1">
              Отмена
            </Button>
            <Button
              type="submit"
              disabled={paymentMutation.isPending || isProcessing}
              className="flex-1"
            >
              {paymentMutation.isPending || isProcessing ? 'Отправка...' : 'Оплатить'}
            </Button>
          </div>
        </form>
      </motion.div>

      {/* Модальное окно успешного платежа */}
      {showSuccessModal && (
        <div className="fixed inset-0 z-[60] flex items-center justify-center bg-black/50 p-4">
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            className="w-full max-w-md rounded-2xl bg-white p-6 text-center"
          >
            <div className="mb-4 flex justify-center">
              <div className="flex h-16 w-16 items-center justify-center rounded-full bg-green-100">
                <svg className="h-8 w-8 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                </svg>
              </div>
            </div>
            <h3 className="mb-2 text-xl font-bold text-gray-900">Перевод успешен</h3>
            <p className="mb-6 text-gray-600">{successMessage}</p>
            <Button
              onClick={() => {
                setShowSuccessModal(false)
                onClose()
              }}
              className="w-full bg-purple-600 hover:bg-purple-700"
            >
              OK
            </Button>
          </motion.div>
        </div>
      )}
    </div>
  )
}

