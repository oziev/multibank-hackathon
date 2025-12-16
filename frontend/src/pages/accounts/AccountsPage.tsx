import { useState } from 'react'
import { motion } from 'framer-motion'
import { MobileHeader } from '@widgets/header'
import { BottomNavigation } from '@widgets/bottom-navigation'
import { AccountList } from '@widgets/account-list'
import { Button, Card, CardContent, Input, Label } from '@shared/ui'
import { useGetAccounts } from '@entities/account'
import { apiClient } from '@shared/api'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { 
  CreditCard, 
  Gift, 
  Plus, 
  Eye, 
  EyeOff, 
  ArrowUpDown,
  Sparkles,
  X
} from 'lucide-react'

type ModalType = 'create-account' | 'loyalty-cards' | 'set-priority' | 'account-settings' | null

export function AccountsPage() {
  const { data: accounts } = useGetAccounts()
  const [activeModal, setActiveModal] = useState<ModalType>(null)
  const queryClient = useQueryClient()

  return (
    <div className="min-h-screen pb-20" style={{ background: 'linear-gradient(135deg, #DBEAFE 0%, #FFFFFF 50%, #E0E7FF 100%)' }}>
      <MobileHeader />

      <main className="container mx-auto px-4 py-6">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
        >
          <h2 className="mb-2 text-3xl font-bold" style={{ background: 'linear-gradient(90deg, #3B82F6 0%, #6366F1 100%)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>
            Счета
          </h2>
          <p className="text-gray-700 text-base font-medium">Управление банковскими счетами</p>
        </motion.div>

        {/* Быстрые действия */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1, duration: 0.5 }}
          className="my-4 grid grid-cols-4 gap-3"
        >
          <ActionButton
            icon={<Plus className="h-5 w-5" />}
            label="Создать счет"
            color="blue"
            onClick={() => setActiveModal('create-account')}
          />
          <ActionButton
            icon={<Gift className="h-5 w-5" />}
            label="Лояльность"
            color="purple"
            onClick={() => setActiveModal('loyalty-cards')}
          />
          <ActionButton
            icon={<ArrowUpDown className="h-5 w-5" />}
            label="Приоритеты"
            color="indigo"
            onClick={() => setActiveModal('set-priority')}
          />
          <ActionButton
            icon={<Sparkles className="h-5 w-5" />}
            color="cyan"
            label="Настройки"
            onClick={() => setActiveModal('account-settings')}
          />
        </motion.div>

        {/* Список счетов */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2, duration: 0.5 }}
        >
          <AccountList />
        </motion.div>
      </main>

      <BottomNavigation />

      {/* Модальные окна */}
      {activeModal === 'create-account' && (
        <CreateAccountModal
          onClose={() => setActiveModal(null)}
          onSuccess={() => {
            setActiveModal(null)
            queryClient.invalidateQueries(['accounts'])
          }}
        />
      )}

      {activeModal === 'loyalty-cards' && (
        <LoyaltyCardsModal
          onClose={() => setActiveModal(null)}
        />
      )}

      {activeModal === 'set-priority' && (
        <SetPriorityModal
          accounts={accounts || []}
          onClose={() => setActiveModal(null)}
          onSuccess={() => {
            setActiveModal(null)
            queryClient.invalidateQueries({ queryKey: ['accounts'] })
          }}
        />
      )}

      {activeModal === 'account-settings' && (
        <AccountSettingsModal
          accounts={accounts || []}
          onClose={() => setActiveModal(null)}
          onSuccess={() => {
            setActiveModal(null)
            queryClient.invalidateQueries({ queryKey: ['accounts'] })
          }}
        />
      )}
    </div>
  )
}
// Кнопка быстрого действия
const actionButtonColors = {
  blue: 'bg-gradient-to-br from-blue-500 to-blue-600 shadow-blue-500/30',
  purple: 'bg-gradient-to-br from-purple-500 to-purple-600 shadow-purple-500/30',
  pink: 'bg-gradient-to-br from-pink-500 to-rose-500 shadow-pink-500/30',
  green: 'bg-gradient-to-br from-green-500 to-emerald-600 shadow-green-500/30',
  default: 'bg-gradient-to-br from-gray-500 to-gray-600 shadow-gray-500/30',
}

const actionButtonInlineStyles = {
  blue: { background: 'linear-gradient(135deg, #3B82F6 0%, #2563EB 100%)', boxShadow: '0 4px 12px rgba(59, 130, 246, 0.3)' },
  purple: { background: 'linear-gradient(135deg, #8B5CF6 0%, #7C3AED 100%)', boxShadow: '0 4px 12px rgba(139, 92, 246, 0.3)' },
  indigo: { background: 'linear-gradient(135deg, #6366F1 0%, #4F46E5 100%)', boxShadow: '0 4px 12px rgba(99, 102, 241, 0.3)' },
  cyan: { background: 'linear-gradient(135deg, #06B6D4 0%, #0891B2 100%)', boxShadow: '0 4px 12px rgba(6, 182, 212, 0.3)' },
  default: { background: 'linear-gradient(135deg, #6B7280 0%, #4B5563 100%)', boxShadow: '0 4px 12px rgba(107, 114, 128, 0.3)' },
}

function ActionButton({ icon, label, color = 'default', onClick }: { icon: React.ReactNode, label: string, color?: keyof typeof actionButtonInlineStyles, onClick: () => void }) {
  return (
    <button
      onClick={onClick}
      style={actionButtonInlineStyles[color]}
      className="flex flex-col items-center gap-1.5 rounded-2xl p-3 text-white transition-all duration-300 hover:scale-105 active:scale-95"
    >
      <div className="text-white">{icon}</div>
      <span className="text-[10px] font-semibold text-center leading-tight">{label}</span>
    </button>
  )
}

// Модалка создания счета
function CreateAccountModal({ onClose, onSuccess }: { onClose: () => void, onSuccess: () => void }) {
  const [selectedBank, setSelectedBank] = useState<number>(1)
  const [accountName, setAccountName] = useState('')
  const [initialBalance, setInitialBalance] = useState('')

  const createMutation = useMutation({
    mutationFn: async (data: any) => {
      return apiClient.post('/api/accounts/create-direct', {
        clientId: data.bankId,
        accountName: data.accountName,
        initialBalance: data.initialBalance
      })
    },
    onSuccess: (data: any) => {
      const accountName = data?.account?.accountName || 'счет'
      alert(`✅ Успешно!\n\n${accountName} создан и готов к использованию!`)
      onSuccess()
    },
    onError: (error: any) => {
      alert(`❌ Ошибка создания счета\n\n${error?.message || 'Попробуйте позже'}`)
    }
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    
    if (!accountName.trim()) {
      alert('❌ Укажите название счета')
      return
    }

    if (accountName.trim().length < 3) {
      alert('❌ Название должно содержать минимум 3 символа')
      return
    }

    const balance = parseFloat(initialBalance) || 0
    if (balance < 0) {
      alert('❌ Начальный баланс не может быть отрицательным')
      return
    }

    if (balance > 10000000) {
      alert('❌ Максимальный начальный баланс: 10 000 000 ₽')
      return
    }

    createMutation.mutate({
      bankId: selectedBank,
      accountName: accountName.trim(),
      initialBalance: balance
    })
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        className="w-full max-w-md rounded-2xl bg-white p-6"
      >
        <div className="mb-4 flex items-center justify-between">
          <h3 className="text-xl font-bold text-gray-900">Создать новый счет</h3>
          <button onClick={onClose} className="rounded-full p-1 hover:bg-gray-100">
            <X className="h-5 w-5" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <Label>Банк</Label>
            <select
              value={selectedBank}
              onChange={(e) => setSelectedBank(parseInt(e.target.value))}
              className="w-full rounded-lg border border-gray-300 px-3 py-2"
            >
              <option value={1}>VBank</option>
              <option value={3}>ABank</option>
              <option value={2}>SBank</option>
            </select>
          </div>

          <div>
            <Label>Название счета</Label>
            <Input
              type="text"
              placeholder="Например: Накопительный счет"
              value={accountName}
              onChange={(e) => setAccountName(e.target.value)}
            />
          </div>

          <div>
            <Label>Начальный баланс (₽)</Label>
            <Input
              type="number"
              placeholder="10000"
              value={initialBalance}
              onChange={(e) => setInitialBalance(e.target.value)}
            />
          </div>

          <div className="flex gap-3 pt-2">
            <Button type="button" variant="outline" onClick={onClose} className="flex-1">
              Отмена
            </Button>
            <Button
              type="submit"
              disabled={createMutation.isPending}
              className="flex-1 bg-purple-600 hover:bg-purple-700"
            >
              {createMutation.isPending ? 'Создание...' : 'Создать'}
            </Button>
          </div>
        </form>
      </motion.div>
    </div>
  )
}

// Модалка карт лояльности
function LoyaltyCardsModal({ onClose }: { onClose: () => void }) {
  const [cards, setCards] = useState<any[]>([])
  const [showAddForm, setShowAddForm] = useState(false)
  const [formData, setFormData] = useState({
    cardType: 'MAGNIT',
    cardNumber: '',
    cardName: ''
  })
  const queryClient = useQueryClient()

  // Загрузка карт
  const { data: cardsData } = useQuery({
    queryKey: ['loyalty-cards'],
    queryFn: () => apiClient.get('/api/loyalty-cards')
  })

  const addCardMutation = useMutation({
    mutationFn: (data: any) => apiClient.post('/api/loyalty-cards', data),
    onSuccess: () => {
      alert('✅ Карта добавлена!')
      queryClient.invalidateQueries(['loyalty-cards'])
      setShowAddForm(false)
      setFormData({ cardType: 'MAGNIT', cardNumber: '', cardName: '' })
    },
    onError: (error: any) => {
      alert(error?.message || 'Ошибка добавления карты')
    }
  })

  const deleteCardMutation = useMutation({
    mutationFn: (cardId: number) => apiClient.delete(`/api/loyalty-cards/${cardId}`),
    onSuccess: () => {
      alert('✅ Карта удалена!')
      queryClient.invalidateQueries(['loyalty-cards'])
    }
  })

  const handleAddCard = (e: React.FormEvent) => {
    e.preventDefault()
    
    if (!formData.cardNumber.trim()) {
      alert('Укажите номер карты')
      return
    }

    addCardMutation.mutate({
      cardType: formData.cardType,
      cardNumber: formData.cardNumber.trim(),
      cardName: formData.cardName.trim() || undefined,
      barcodeType: 'EAN13'
    })
  }

  const loyaltyCards = cardsData?.cards || []

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4 overflow-y-auto">
      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        className="w-full max-w-md rounded-2xl bg-white p-6 my-8"
      >
        <div className="mb-4 flex items-center justify-between">
          <h3 className="text-xl font-bold text-gray-900">💳 Карты лояльности</h3>
          <button onClick={onClose} className="rounded-full p-1 hover:bg-gray-100">
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Список карт */}
        <div className="space-y-3 mb-4">
          {loyaltyCards.length === 0 ? (
            <div className="text-center py-8 text-gray-500">
              <Gift className="h-12 w-12 mx-auto mb-2 text-gray-300" />
              <p>У вас пока нет карт лояльности</p>
            </div>
          ) : (
            loyaltyCards.map((card: any) => (
              <Card key={card.id}>
                <CardContent className="p-3 flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className="text-2xl">
                      {getCardIcon(card.cardType)}
                    </div>
                    <div>
                      <p className="font-medium text-sm">{card.cardName || getCardTypeName(card.cardType)}</p>
                      <p className="text-xs text-gray-500">{card.maskedNumber}</p>
                    </div>
                  </div>
                  <button
                    onClick={() => {
                      if (confirm('Удалить эту карту?')) {
                        deleteCardMutation.mutate(card.id)
                      }
                    }}
                    className="text-red-500 hover:text-red-700 text-xs"
                  >
                    Удалить
                  </button>
                </CardContent>
              </Card>
            ))
          )}
        </div>

        {/* Форма добавления */}
        {!showAddForm ? (
          <Button
            onClick={() => setShowAddForm(true)}
            className="w-full border-dashed"
            variant="outline"
          >
            <Plus className="mr-2 h-4 w-4" />
            Добавить карту
          </Button>
        ) : (
          <form onSubmit={handleAddCard} className="space-y-3 border-t pt-4">
            <div>
              <Label>Тип карты</Label>
              <select
                value={formData.cardType}
                onChange={(e) => setFormData({ ...formData, cardType: e.target.value })}
                className="w-full rounded-lg border px-3 py-2 text-sm"
              >
                <option value="MAGNIT">🛒 Магнит</option>
                <option value="PYATEROCHKA">🍎 Пятёрочка</option>
                <option value="LENTA">🏪 Лента</option>
                <option value="AUCHAN">🛍️ Ашан</option>
                <option value="LETUAL">💄 Летуаль</option>
                <option value="GOLDEN_APPLE">💎 Золотое Яблоко</option>
                <option value="OTHER">💳 Другая</option>
              </select>
            </div>

            <div>
              <Label>Номер карты</Label>
              <Input
                type="text"
                placeholder="1234567890123"
                value={formData.cardNumber}
                onChange={(e) => setFormData({ ...formData, cardNumber: e.target.value })}
              />
            </div>

            <div>
              <Label>Название (опционально)</Label>
              <Input
                type="text"
                placeholder="Моя карта Магнит"
                value={formData.cardName}
                onChange={(e) => setFormData({ ...formData, cardName: e.target.value })}
              />
            </div>

            <div className="flex gap-2">
              <Button
                type="button"
                variant="outline"
                onClick={() => setShowAddForm(false)}
                className="flex-1"
                size="sm"
              >
                Отмена
              </Button>
              <Button
                type="submit"
                disabled={addCardMutation.isPending}
                className="flex-1 bg-purple-600"
                size="sm"
              >
                {addCardMutation.isPending ? 'Добавление...' : 'Добавить'}
              </Button>
            </div>
          </form>
        )}
      </motion.div>
    </div>
  )
}

// Модалка установки приоритетов
function SetPriorityModal({ 
  accounts, 
  onClose, 
  onSuccess 
}: { 
  accounts: any[], 
  onClose: () => void, 
  onSuccess: () => void 
}) {
  const [priorities, setPriorities] = useState<Record<string | number, number>>(
    accounts.reduce((acc, account, idx) => {
      const accountKey = account.id || `${account.clientId}-${account.accountId}`
      return {
        ...acc,
        [accountKey]: idx + 1
      }
    }, {} as Record<string | number, number>)
  )

  const saveMutation = useMutation({
    mutationFn: async () => {
      const promises = Object.entries(priorities).map(([accountKey, priority]) => {
        // Если accountKey это число (ID), используем его, иначе ищем account по ключу
        const account = accounts.find(acc => {
          const key = acc.id || `${acc.clientId}-${acc.accountId}`
          return String(key) === String(accountKey)
        })
        if (account && account.id) {
          return apiClient.put(`/api/accounts/${account.id}/priority?priority=${priority}`)
        }
        return Promise.resolve()
      })
      return Promise.all(promises)
    },
    onSuccess: () => {
      alert('✅ Приоритеты обновлены!')
      onSuccess()
    },
    onError: (error: any) => {
      alert(error?.message || 'Ошибка сохранения приоритетов')
    }
  })

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        className="w-full max-w-md rounded-2xl bg-white p-6 max-h-[80vh] overflow-y-auto"
      >
        <div className="mb-4 flex items-center justify-between">
          <h3 className="text-xl font-bold text-gray-900">Приоритет списания</h3>
          <button onClick={onClose} className="rounded-full p-1 hover:bg-gray-100">
            <X className="h-5 w-5" />
          </button>
        </div>

        <p className="mb-4 text-sm text-gray-600">
          Установите порядок списания при автоплатежах. 1 = первым списывается.
        </p>

        <div className="space-y-3 mb-4">
          {accounts.map((account) => {
            const accountKey = account.id || `${account.clientId}-${account.accountId}`
            return (
              <Card key={`priority-${accountKey}`}>
                <CardContent className="p-3">
                  <div className="flex items-center justify-between">
                    <div className="flex-1">
                      <p className="font-medium text-sm">{account.accountName}</p>
                      <p className="text-xs text-gray-500">{account.clientName}</p>
                    </div>
                    <div className="flex items-center gap-2">
                      <input
                        type="number"
                        min={1}
                        max={10}
                        value={priorities[accountKey] || 1}
                        onChange={(e) => {
                          const newPriorities = { ...priorities }
                          newPriorities[accountKey] = parseInt(e.target.value) || 1
                          setPriorities(newPriorities)
                        }}
                        className="w-16 rounded border border-gray-300 px-2 py-1 text-center text-sm"
                      />
                    </div>
                  </div>
                </CardContent>
              </Card>
            )
          })}
        </div>

        <div className="flex gap-3">
          <Button type="button" variant="outline" onClick={onClose} className="flex-1">
            Отмена
          </Button>
          <Button
            onClick={() => saveMutation.mutate()}
            disabled={saveMutation.isPending}
            className="flex-1 bg-purple-600 hover:bg-purple-700"
          >
            {saveMutation.isPending ? 'Сохранение...' : 'Сохранить'}
          </Button>
        </div>
      </motion.div>
    </div>
  )
}

// Модалка настроек счетов
function AccountSettingsModal({
  accounts,
  onClose,
  onSuccess
}: {
  accounts: any[]
  onClose: () => void
  onSuccess: () => void
}) {
  const [selectedAction, setSelectedAction] = useState<'rename' | 'sync' | 'hide' | null>(null)
  const [selectedAccount, setSelectedAccount] = useState<any>(null)
  const [newName, setNewName] = useState('')
  const queryClient = useQueryClient()

  const renameMutation = useMutation({
    mutationFn: async ({ accountId, newName }: { accountId: number, newName: string }) => {
      return apiClient.put(`/api/accounts/${accountId}/rename`, { accountName: newName })
    },
    onSuccess: () => {
      alert('✅ Счет успешно переименован!')
      queryClient.invalidateQueries({ queryKey: ['accounts'] })
      onSuccess()
    },
    onError: (error: any) => {
      alert(error?.message || 'Ошибка переименования счета')
    }
  })

  const hideMutation = useMutation({
    mutationFn: async (accountId: number) => {
      return apiClient.put(`/api/accounts/${accountId}/toggle-visibility`)
    },
    onSuccess: () => {
      alert('✅ Баланс счета скрыт!')
      queryClient.invalidateQueries({ queryKey: ['accounts'] })
      onSuccess()
    },
    onError: (error: any) => {
      alert(error?.message || 'Ошибка скрытия баланса')
    }
  })

  const syncMutation = useMutation({
    mutationFn: async (accountId: number) => {
      return apiClient.post(`/api/accounts/${accountId}/sync`)
    },
    onSuccess: () => {
      alert('✅ Счет успешно синхронизирован!')
      queryClient.invalidateQueries({ queryKey: ['accounts'] })
      onSuccess()
    },
    onError: (error: any) => {
      alert(error?.message || 'Ошибка синхронизации счета')
    }
  })

  if (!selectedAction) {
    return (
      <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          className="w-full max-w-md rounded-2xl bg-white p-6"
        >
          <div className="mb-4 flex items-center justify-between">
            <h3 className="text-xl font-bold text-gray-900">Настройки счетов</h3>
            <button onClick={onClose} className="rounded-full p-1 hover:bg-gray-100">
              <X className="h-5 w-5" />
            </button>
          </div>

          <div className="space-y-3">
            <button
              onClick={() => setSelectedAction('rename')}
              className="w-full flex items-center gap-3 p-4 rounded-lg border border-gray-200 hover:bg-gray-50 transition-colors"
            >
              <div className="w-10 h-10 rounded-full bg-blue-100 flex items-center justify-center">
                <span className="text-blue-600 font-semibold">📝</span>
              </div>
              <div className="flex-1 text-left">
                <div className="font-medium text-gray-900">Переименовать счет</div>
                <div className="text-sm text-gray-500">Изменить название счета</div>
              </div>
            </button>

            <button
              onClick={() => setSelectedAction('sync')}
              className="w-full flex items-center gap-3 p-4 rounded-lg border border-gray-200 hover:bg-gray-50 transition-colors"
            >
              <div className="w-10 h-10 rounded-full bg-green-100 flex items-center justify-center">
                <span className="text-green-600 font-semibold">🔄</span>
              </div>
              <div className="flex-1 text-left">
                <div className="font-medium text-gray-900">Синхронизация</div>
                <div className="text-sm text-gray-500">Обновить данные счета</div>
              </div>
            </button>

            <button
              onClick={() => setSelectedAction('hide')}
              className="w-full flex items-center gap-3 p-4 rounded-lg border border-gray-200 hover:bg-gray-50 transition-colors"
            >
              <div className="w-10 h-10 rounded-full bg-purple-100 flex items-center justify-center">
                <span className="text-purple-600 font-semibold">👁️</span>
              </div>
              <div className="flex-1 text-left">
                <div className="font-medium text-gray-900">Скрытие баланса</div>
                <div className="text-sm text-gray-500">Скрыть баланс счета</div>
              </div>
            </button>
          </div>

          <div className="mt-4">
            <Button variant="outline" onClick={onClose} className="w-full">
              Отмена
            </Button>
          </div>
        </motion.div>
      </div>
    )
  }

  if (!selectedAccount) {
    return (
      <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          className="w-full max-w-md rounded-2xl bg-white p-6 max-h-[80vh] overflow-y-auto"
        >
          <div className="mb-4 flex items-center justify-between">
            <h3 className="text-xl font-bold text-gray-900">
              {selectedAction === 'rename' && 'Переименовать счет'}
              {selectedAction === 'sync' && 'Синхронизация счета'}
              {selectedAction === 'hide' && 'Скрыть баланс'}
            </h3>
            <button onClick={() => setSelectedAction(null)} className="rounded-full p-1 hover:bg-gray-100">
              <X className="h-5 w-5" />
            </button>
          </div>

          <p className="mb-4 text-sm text-gray-600">Выберите счет:</p>

          <div className="space-y-2 mb-4">
            {accounts.map((account) => (
              <button
                key={account.id || `${account.clientId}-${account.accountId}`}
                onClick={() => setSelectedAccount(account)}
                className="w-full p-3 rounded-lg border border-gray-200 hover:bg-gray-50 text-left transition-colors"
              >
                <div className="font-medium text-gray-900">{account.accountName}</div>
                <div className="text-sm text-gray-500">{account.clientName}</div>
              </button>
            ))}
          </div>

          <Button variant="outline" onClick={() => setSelectedAction(null)} className="w-full">
            Назад
          </Button>
        </motion.div>
      </div>
    )
  }

  // Финальный шаг - выполнение действия
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        className="w-full max-w-md rounded-2xl bg-white p-6"
      >
        <div className="mb-4 flex items-center justify-between">
          <h3 className="text-xl font-bold text-gray-900">
            {selectedAction === 'rename' && 'Переименовать счет'}
            {selectedAction === 'sync' && 'Синхронизация'}
            {selectedAction === 'hide' && 'Скрыть баланс'}
          </h3>
          <button onClick={onClose} className="rounded-full p-1 hover:bg-gray-100">
            <X className="h-5 w-5" />
          </button>
        </div>

        <div className="mb-4 p-3 bg-gray-50 rounded-lg">
          <div className="text-sm text-gray-600 mb-1">Выбранный счет:</div>
          <div className="font-medium text-gray-900">{selectedAccount.accountName}</div>
          <div className="text-xs text-gray-500">{selectedAccount.clientName}</div>
        </div>

        {selectedAction === 'rename' && (
          <div className="mb-4">
            <Label>Новое название счета</Label>
            <Input
              type="text"
              value={newName}
              onChange={(e) => setNewName(e.target.value)}
              placeholder={selectedAccount.accountName}
              className="mt-1"
            />
          </div>
        )}

        {selectedAction === 'sync' && (
          <div className="mb-4 p-4 bg-blue-50 rounded-lg">
            <p className="text-sm text-gray-700">
              Счет будет синхронизирован с банком. Это может занять несколько секунд.
            </p>
          </div>
        )}

        {selectedAction === 'hide' && (
          <div className="mb-4 p-4 bg-orange-50 rounded-lg">
            <p className="text-sm text-gray-700">
              Баланс этого счета будет скрыт. Вы сможете отобразить его позже в настройках.
            </p>
          </div>
        )}

        <div className="flex gap-3">
          <Button variant="outline" onClick={() => setSelectedAccount(null)} className="flex-1">
            Назад
          </Button>
          <Button
            onClick={() => {
              if (selectedAction === 'rename') {
                if (!newName.trim()) {
                  alert('❌ Введите новое название счета')
                  return
                }
                renameMutation.mutate({ accountId: selectedAccount.id, newName: newName.trim() })
              } else if (selectedAction === 'sync') {
                syncMutation.mutate(selectedAccount.id)
              } else if (selectedAction === 'hide') {
                hideMutation.mutate(selectedAccount.id)
              }
            }}
            disabled={renameMutation.isPending || syncMutation.isPending || hideMutation.isPending}
            className="flex-1 bg-purple-600 hover:bg-purple-700"
          >
            {renameMutation.isPending || syncMutation.isPending || hideMutation.isPending
              ? 'Обработка...'
              : selectedAction === 'rename'
              ? 'Переименовать'
              : selectedAction === 'sync'
              ? 'Синхронизировать'
              : 'Скрыть'}
          </Button>
        </div>
      </motion.div>
    </div>
  )
}

// Хелперы для карт лояльности
function getCardIcon(type: string): string {
  const icons: Record<string, string> = {
    MAGNIT: '🛒',
    PYATEROCHKA: '🍎',
    LENTA: '🏪',
    AUCHAN: '🛍️',
    LETUAL: '💄',
    GOLDEN_APPLE: '💎',
    RIVEGAUCHE: '🎨',
    AZBUKA_VKUSA: '🥗',
    OTHER: '💳'
  }
  return icons[type] || '💳'
}

function getCardTypeName(type: string): string {
  const names: Record<string, string> = {
    MAGNIT: 'Магнит',
    PYATEROCHKA: 'Пятёрочка',
    LENTA: 'Лента',
    AUCHAN: 'Ашан',
    LETUAL: 'Летуаль',
    GOLDEN_APPLE: 'Золотое Яблоко',
    RIVEGAUCHE: 'Рив Гош',
    AZBUKA_VKUSA: 'Азбука Вкуса',
    OTHER: 'Другая карта'
  }
  return names[type] || type
}

// Импорт useQuery
import { useQuery } from '@tanstack/react-query'

