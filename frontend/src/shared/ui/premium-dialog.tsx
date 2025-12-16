import { useNavigate } from 'react-router-dom'
import { X, Crown, Check } from 'lucide-react'
import { Button } from './button'
import { ROUTES } from '@shared/config'

type PremiumDialogProps = {
  isOpen: boolean
  onClose: () => void
  reason: 'groups' | 'members'
}

export function PremiumDialog({ isOpen, onClose, reason }: PremiumDialogProps) {
  const navigate = useNavigate()

  if (!isOpen) return null

  const title = reason === 'groups' ? 'Лимит групп исчерпан' : 'Лимит участников исчерпан'
  const description =
    reason === 'groups'
      ? 'В бесплатной версии вы можете создать только 1 группу'
      : 'В бесплатной версии в группе может быть максимум 2 участника'

  const features = [
    'До 5 групп',
    'До 20 участников в группе',
    'Приоритетная поддержка',
    'Расширенная аналитика',
  ]

  const handleUpgrade = () => {
    onClose()
    navigate(ROUTES.PREMIUM)
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4">
      <div className="w-full max-w-md rounded-2xl bg-gradient-to-br from-purple-50 to-blue-50 shadow-2xl">
        {/* Header */}
        <div className="relative border-b border-purple-200 p-6 pb-4">
          <button
            onClick={onClose}
            className="absolute top-4 right-4 rounded-lg p-1 text-gray-400 hover:bg-white/50 hover:text-gray-600"
          >
            <X className="h-5 w-5" />
          </button>
          <div className="mb-2 flex items-center gap-2">
            <div className="flex h-12 w-12 items-center justify-center rounded-full bg-gradient-to-br from-purple-600 to-blue-600">
              <Crown className="h-6 w-6 text-white" />
            </div>
            <div>
              <h2 className="text-xl font-bold text-gray-900">{title}</h2>
              <p className="text-sm text-gray-600">{description}</p>
            </div>
          </div>
        </div>

        {/* Content */}
        <div className="p-6">
          <div className="mb-6 rounded-xl bg-white p-4 shadow-sm">
            <div className="mb-3 flex items-baseline gap-2">
              <span className="text-4xl font-bold text-gray-900">299 ₽</span>
              <span className="text-sm text-gray-500">/ месяц</span>
            </div>
            <p className="text-sm text-gray-600">Получите Premium и продолжайте работу</p>
          </div>

          <div className="mb-6 space-y-3">
            <p className="text-sm font-semibold text-gray-900">Что вы получите:</p>
            {features.map((feature, index) => (
              <div key={index} className="flex items-center gap-3">
                <div className="flex h-5 w-5 items-center justify-center rounded-full bg-green-100">
                  <Check className="h-3 w-3 text-green-600" />
                </div>
                <p className="text-sm text-gray-700">{feature}</p>
              </div>
            ))}
          </div>

          <div className="space-y-2">
            <Button
              onClick={handleUpgrade}
              className="w-full bg-gradient-to-r from-purple-600 to-blue-600 py-6 text-base font-semibold text-white shadow-lg hover:from-purple-700 hover:to-blue-700"
            >
              Перейти на Premium
            </Button>
            <Button
              variant="outline"
              onClick={onClose}
              className="w-full border-gray-300 text-gray-600"
            >
              Может позже
            </Button>
          </div>

          <p className="mt-4 text-center text-xs text-gray-500">
            Подписка продлевается автоматически. Отменить можно в любой момент.
          </p>
        </div>
      </div>
    </div>
  )
}
