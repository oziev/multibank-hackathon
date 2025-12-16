import { useState } from 'react'
import { motion } from 'framer-motion'
import { MobileHeader } from '@widgets/header'
import { BottomNavigation } from '@widgets/bottom-navigation'
import { useGetMe } from '@entities/user'
import { Button, Card, CardContent } from '@shared/ui'
import { apiClient } from '@shared/api'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Copy, Gift, Users, TrendingUp, CheckCircle, XCircle } from 'lucide-react'

interface ReferralStats {
  referral_code: string
  total_referrals: number
  total_rewards: number
  pending_rewards: number
  can_claim: boolean
  min_claim_amount: number
}

interface Referral {
  id: number
  referred_user_id: number
  referred_user_email: string
  status: string
  reward_amount: number
  created_at: string
}

export function ReferralsPage() {
  const { data: user } = useGetMe()
  const queryClient = useQueryClient()
  const [copied, setCopied] = useState(false)

  const { data: stats, isLoading: statsLoading, refetch: refetchStats } = useQuery({
    queryKey: ['referrals', 'stats'],
    queryFn: async () => {
      const response = await apiClient.get('/api/referrals/stats')
      // API возвращает { success: true, data: {...} }
      // response уже содержит data из base-client
      return response as ReferralStats
    },
  })

  const { data: referrals, isLoading: referralsLoading } = useQuery({
    queryKey: ['referrals', 'list'],
    queryFn: async () => {
      const response = await apiClient.get('/api/referrals/list')
      // API возвращает { success: true, data: { referrals: [...] } }
      return (response as any).referrals || []
    },
  })

  const claimMutation = useMutation({
    mutationFn: () => apiClient.post('/api/referrals/claim-reward'),
    onSuccess: () => {
      alert('✅ Запрос на выплату успешно отправлен!')
      queryClient.invalidateQueries({ queryKey: ['referrals'] })
    },
    onError: (error: any) => {
      alert(`❌ Ошибка: ${error?.message || 'Не удалось запросить выплату'}`)
    },
  })

  const copyToClipboard = async (text: string) => {
    try {
      await navigator.clipboard.writeText(text)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    } catch (err) {
      console.error('Failed to copy:', err)
    }
  }

  const referralLink = stats?.referral_code
    ? `${window.location.origin}/sign-up?ref=${stats.referral_code}`
    : ''

  return (
    <div className="min-h-screen bg-gray-50 pb-20">
      <MobileHeader title="Реферальная программа" />
      
      <div className="px-4 pt-4 space-y-4">
        {/* Статистика */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3 }}
        >
          <Card>
            <CardContent className="p-6">
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <h2 className="text-lg font-semibold text-gray-900">Ваша статистика</h2>
                  <Gift className="w-6 h-6 text-blue-600" />
                </div>
                
                {statsLoading ? (
                  <div className="text-center py-4">Загрузка...</div>
                ) : (
                  <div className="grid grid-cols-2 gap-4">
                    <div className="bg-blue-50 rounded-lg p-4">
                      <div className="text-sm text-gray-600 mb-1">Рефералов</div>
                      <div className="text-2xl font-bold text-blue-600">
                        {stats?.total_referrals || 0}
                      </div>
                    </div>
                    <div className="bg-green-50 rounded-lg p-4">
                      <div className="text-sm text-gray-600 mb-1">Награды</div>
                      <div className="text-2xl font-bold text-green-600">
                        {stats?.pending_rewards ? `${stats.pending_rewards.toFixed(2)}₽` : '0₽'}
                      </div>
                    </div>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        </motion.div>

        {/* Реферальный код */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3, delay: 0.1 }}
        >
          <Card>
            <CardContent className="p-6">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold text-gray-900">Ваш реферальный код</h3>
                      <Button
                        onClick={async () => {
                          // Генерируем или обновляем код через API
                          try {
                            if (stats?.referral_code) {
                              // Обновляем существующий код
                              await apiClient.post('/api/referrals/regenerate-code')
                            } else {
                              // Создаем новый код
                              await apiClient.get('/api/referrals/my-code')
                            }
                            // Обновляем данные
                            await refetchStats()
                          } catch (error: any) {
                            alert('❌ Ошибка: ' + (error?.message || 'Не удалось сгенерировать код'))
                          }
                        }}
                        className="bg-blue-600 hover:bg-blue-700"
                        size="sm"
                      >
                        {stats?.referral_code ? 'Обновить' : 'Сгенерировать'}
                      </Button>
              </div>
              
              {stats?.referral_code ? (
                <>
                  <div className="flex items-center gap-2 mb-4">
                    <input
                      type="text"
                      value={stats.referral_code}
                      readOnly
                      className="flex-1 px-4 py-2 border border-gray-300 rounded-lg bg-gray-50 font-mono text-sm"
                    />
                    <Button
                      onClick={() => copyToClipboard(stats.referral_code)}
                      className="px-4"
                    >
                      {copied ? <CheckCircle className="w-5 h-5" /> : <Copy className="w-5 h-5" />}
                    </Button>
                  </div>
                  <div className="text-sm text-gray-600 mb-2">Или поделитесь ссылкой:</div>
                  <div className="flex items-center gap-2">
                    <input
                      type="text"
                      value={referralLink}
                      readOnly
                      className="flex-1 px-4 py-2 border border-gray-300 rounded-lg bg-gray-50 text-xs"
                    />
                    <Button
                      onClick={() => copyToClipboard(referralLink)}
                      className="px-4"
                    >
                      {copied ? <CheckCircle className="w-5 h-5" /> : <Copy className="w-5 h-5" />}
                    </Button>
                  </div>
                </>
              ) : (
                <div className="text-center py-4 text-gray-500">
                  Нажмите "Сгенерировать" для создания реферального кода
                </div>
              )}
            </CardContent>
          </Card>
        </motion.div>

        {/* Условия */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3, delay: 0.2 }}
        >
          <Card>
            <CardContent className="p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Как это работает?</h3>
              <div className="space-y-3 text-sm text-gray-600">
                <div className="flex items-start gap-3">
                  <div className="w-6 h-6 rounded-full bg-blue-100 flex items-center justify-center flex-shrink-0 mt-0.5">
                    <span className="text-blue-600 font-semibold text-xs">1</span>
                  </div>
                  <div>
                    <div className="font-medium text-gray-900">Пригласите друга</div>
                    <div>Поделитесь своей реферальной ссылкой</div>
                  </div>
                </div>
                <div className="flex items-start gap-3">
                  <div className="w-6 h-6 rounded-full bg-blue-100 flex items-center justify-center flex-shrink-0 mt-0.5">
                    <span className="text-blue-600 font-semibold text-xs">2</span>
                  </div>
                  <div>
                    <div className="font-medium text-gray-900">Получите награды</div>
                    <div>50₽ за регистрацию друга, 100₽ за покупку Premium</div>
                  </div>
                </div>
                <div className="flex items-start gap-3">
                  <div className="w-6 h-6 rounded-full bg-blue-100 flex items-center justify-center flex-shrink-0 mt-0.5">
                    <span className="text-blue-600 font-semibold text-xs">3</span>
                  </div>
                  <div>
                    <div className="font-medium text-gray-900">Выведите средства</div>
                    <div>Минимальная сумма для вывода: {stats?.min_claim_amount || 500}₽</div>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </motion.div>

        {/* Кнопка вывода */}
        {stats?.can_claim && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.3, delay: 0.3 }}
          >
            <Button
              onClick={() => claimMutation.mutate()}
              disabled={claimMutation.isPending}
              className="w-full bg-green-600 hover:bg-green-700"
            >
              {claimMutation.isPending ? 'Обработка...' : `Запросить выплату ${stats.pending_rewards.toFixed(2)}₽`}
            </Button>
          </motion.div>
        )}

        {/* Список рефералов */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3, delay: 0.4 }}
        >
          <Card>
            <CardContent className="p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
                <Users className="w-5 h-5" />
                Ваши рефералы
              </h3>
              
              {referralsLoading ? (
                <div className="text-center py-4">Загрузка...</div>
              ) : referrals && referrals.length > 0 ? (
                <div className="space-y-3">
                  {referrals.map((ref) => (
                    <div
                      key={ref.id}
                      className="flex items-center justify-between p-3 bg-gray-50 rounded-lg"
                    >
                      <div className="flex-1">
                        <div className="font-medium text-gray-900">
                          {ref.referred_user_email}
                        </div>
                        <div className="text-sm text-gray-600">
                          {new Date(ref.created_at).toLocaleDateString('ru-RU')}
                        </div>
                      </div>
                      <div className="text-right">
                        {ref.status === 'completed' ? (
                          <div className="flex items-center gap-1 text-green-600">
                            <CheckCircle className="w-4 h-4" />
                            <span className="font-semibold">+{ref.reward_amount}₽</span>
                          </div>
                        ) : (
                          <div className="flex items-center gap-1 text-gray-400">
                            <XCircle className="w-4 h-4" />
                            <span className="text-sm">Ожидание</span>
                          </div>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-8 text-gray-500">
                  <Users className="w-12 h-12 mx-auto mb-2 opacity-50" />
                  <div>Пока нет рефералов</div>
                  <div className="text-sm mt-1">Пригласите друзей и получите награды!</div>
                </div>
              )}
            </CardContent>
          </Card>
        </motion.div>
      </div>

      <BottomNavigation />
    </div>
  )
}

