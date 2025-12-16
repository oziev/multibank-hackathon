import { useState } from 'react'
import { motion } from 'framer-motion'
import { MobileHeader } from '@widgets/header'
import { BottomNavigation } from '@widgets/bottom-navigation'
import { Card, CardContent, Button, Input, Label } from '@shared/ui'
import { apiClient } from '@shared/api'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Gift, Plus, X, CreditCard } from 'lucide-react'

export function LoyaltyCardsPage() {
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
    onSuccess: (data: any) => {
      const cardName = getCardTypeName(formData.cardType)
      alert(`✅ Успешно!\n\n${cardName} добавлена в ваш кошелек!`)
      queryClient.invalidateQueries({ queryKey: ['loyalty-cards'] })
      setShowAddForm(false)
      setFormData({ cardType: 'MAGNIT', cardNumber: '', cardName: '' })
    },
    onError: (error: any) => {
      alert(`❌ Ошибка добавления карты\n\n${error?.message || 'Попробуйте позже'}`)
    }
  })

  const deleteCardMutation = useMutation({
    mutationFn: (cardId: number) => apiClient.delete(`/api/loyalty-cards/${cardId}`),
    onSuccess: (data: any) => {
      alert(`✅ Карта удалена!\n\nОна больше не отображается в списке`)
      queryClient.invalidateQueries({ queryKey: ['loyalty-cards'] })
    },
    onError: (error: any) => {
      alert(`❌ Ошибка удаления карты\n\n${error?.message || 'Попробуйте позже'}`)
    }
  })

  const handleAddCard = (e: React.FormEvent) => {
    e.preventDefault()
    
    if (!formData.cardNumber.trim()) {
      alert('❌ Укажите номер карты')
      return
    }

    const cardNumber = formData.cardNumber.trim()
    if (cardNumber.length < 8) {
      alert('❌ Номер карты должен содержать минимум 8 символов')
      return
    }

    if (!/^\d+$/.test(cardNumber)) {
      alert('❌ Номер карты должен содержать только цифры')
      return
    }

    addCardMutation.mutate({
      cardType: formData.cardType,
      cardNumber: cardNumber,
      cardName: formData.cardName.trim() || undefined,
      barcodeType: 'EAN13'
    })
  }

  const loyaltyCards = cardsData?.cards || []

  return (
    <div className="min-h-screen bg-gray-50 pb-20">
      <MobileHeader />

      <main className="container mx-auto px-4 py-6">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
          className="mb-6"
        >
          <h2 className="mb-2 text-2xl font-bold text-gray-900">Карты лояльности</h2>
          <p className="text-gray-600">Управление дисконтными картами</p>
        </motion.div>

        {/* Список карт */}
        <div className="space-y-3 mb-6">
          {loyaltyCards.length === 0 ? (
            <Card>
              <CardContent className="p-8 text-center">
                <Gift className="h-12 w-12 mx-auto mb-2 text-gray-300" />
                <p className="text-gray-500">У вас пока нет карт лояльности</p>
                <p className="text-sm text-gray-400 mt-1">Добавьте карты магазинов для удобного хранения</p>
              </CardContent>
            </Card>
          ) : (
            loyaltyCards.map((card: any) => (
              <Card key={card.id}>
                <CardContent className="p-4 flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className="text-3xl">
                      {getCardIcon(card.cardType)}
                    </div>
                    <div>
                      <p className="font-medium">{card.cardName || getCardTypeName(card.cardType)}</p>
                      <p className="text-sm text-gray-500">{card.maskedNumber}</p>
                    </div>
                  </div>
                  <button
                    onClick={() => {
                      if (confirm('Удалить эту карту?')) {
                        deleteCardMutation.mutate(card.id)
                      }
                    }}
                    className="text-red-500 hover:text-red-700 text-sm"
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
          <Card>
            <CardContent className="p-4">
              <form onSubmit={handleAddCard} className="space-y-3">
                <div>
                  <Label>Тип карты</Label>
                  <select
                    value={formData.cardType}
                    onChange={(e) => setFormData({ ...formData, cardType: e.target.value })}
                    className="w-full rounded-lg border px-3 py-2"
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

                <div className="flex gap-2 pt-2">
                  <Button
                    type="button"
                    variant="outline"
                    onClick={() => setShowAddForm(false)}
                    className="flex-1"
                  >
                    Отмена
                  </Button>
                  <Button
                    type="submit"
                    disabled={addCardMutation.isPending}
                    className="flex-1"
                  >
                    {addCardMutation.isPending ? 'Добавление...' : 'Добавить'}
                  </Button>
                </div>
              </form>
            </CardContent>
          </Card>
        )}
      </main>

      <BottomNavigation />
    </div>
  )
}

function getCardIcon(type: string): string {
  const icons: Record<string, string> = {
    MAGNIT: '🛒',
    PYATEROCHKA: '🍎',
    LENTA: '🏪',
    AUCHAN: '🛍️',
    LETUAL: '💄',
    GOLDEN_APPLE: '💎',
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
    OTHER: 'Другая карта'
  }
  return names[type] || type
}

