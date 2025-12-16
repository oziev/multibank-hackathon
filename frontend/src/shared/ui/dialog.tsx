import { ReactNode } from 'react'
import { X } from 'lucide-react'
import { Button } from './button'

type DialogProps = {
  isOpen: boolean
  onClose: () => void
  title: string
  description?: string
  children?: ReactNode
  onConfirm?: () => void
  confirmText?: string
  confirmVariant?: 'default' | 'destructive'
  isLoading?: boolean
}

export function Dialog({
  isOpen,
  onClose,
  title,
  description,
  children,
  onConfirm,
  confirmText = 'Подтвердить',
  confirmVariant = 'default',
  isLoading = false,
}: DialogProps) {
  if (!isOpen) return null

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
      <div className="w-full max-w-md rounded-lg bg-white shadow-xl">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-gray-200 p-4">
          <h2 className="text-lg font-semibold text-gray-900">{title}</h2>
          <button
            onClick={onClose}
            className="rounded-lg p-1 text-gray-400 hover:bg-gray-100 hover:text-gray-600"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Content */}
        <div className="p-4">
          {description && <p className="text-sm text-gray-600">{description}</p>}
          {children}
        </div>

        {/* Footer */}
        {onConfirm && (
          <div className="flex gap-2 border-t border-gray-200 p-4">
            <Button variant="outline" onClick={onClose} className="flex-1" disabled={isLoading}>
              Отмена
            </Button>
            <Button
              onClick={onConfirm}
              className={`flex-1 ${
                confirmVariant === 'destructive'
                  ? 'bg-red-600 text-white hover:bg-red-700'
                  : 'bg-blue-600 text-white hover:bg-blue-700'
              }`}
              disabled={isLoading}
            >
              {isLoading ? 'Загрузка...' : confirmText}
            </Button>
          </div>
        )}
      </div>
    </div>
  )
}
