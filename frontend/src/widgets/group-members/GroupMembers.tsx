import { useState } from 'react'
import { useInviteToGroup, useGetGroupSettings } from '@entities/group'
import { Button, Input, Dialog, PremiumDialog } from '@shared/ui'
import { UserPlus, AlertCircle } from 'lucide-react'

type GroupMembersProps = {
  groupId: number
  ownerId: number
  currentUserId: number
}

export function GroupMembers({ groupId, ownerId, currentUserId }: GroupMembersProps) {
  const { data: settings } = useGetGroupSettings()
  const inviteToGroup = useInviteToGroup()

  const [showInviteDialog, setShowInviteDialog] = useState(false)
  const [email, setEmail] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [showPremiumDialog, setShowPremiumDialog] = useState(false)

  const isOwner = currentUserId === ownerId

  // TODO: Get actual member count from API
  const currentMembersCount = 1 // Placeholder
  const canInviteMore = !settings || currentMembersCount < settings.maxMembers

  const validateEmail = (email: string) => {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
    return emailRegex.test(email)
  }

  const handleInvite = () => {
    setError(null)

    if (!email.trim()) {
      setError('Введите email')
      return
    }

    if (!validateEmail(email)) {
      setError('Неверный формат email')
      return
    }

    inviteToGroup.mutate(
      { groupId, email },
      {
        onSuccess: () => {
          setEmail('')
          setShowInviteDialog(false)
        },
        onError: (error: Error) => {
          setError(error.message || 'Ошибка при отправке приглашения')
        },
      }
    )
  }

  const handleInviteClick = () => {
    if (!canInviteMore) {
      setShowPremiumDialog(true)
    } else {
      setShowInviteDialog(true)
    }
  }

  if (!isOwner) return null

  return (
    <>
      <Button
        size="sm"
        onClick={handleInviteClick}
        className="bg-blue-600 text-white hover:bg-blue-700"
      >
        <UserPlus className="mr-1 h-4 w-4" />
        Пригласить
      </Button>

      <Dialog
        isOpen={showInviteDialog}
        onClose={() => {
          setShowInviteDialog(false)
          setEmail('')
          setError(null)
        }}
        title="Пригласить участника"
        description="Введите email пользователя, которого хотите пригласить в группу"
      >
        <div className="space-y-4 pt-4">
          <div>
            <label className="mb-2 block text-sm font-medium text-gray-900">Email участника</label>
            <Input
              type="email"
              value={email}
              onChange={(e) => {
                setEmail(e.target.value)
                setError(null)
              }}
              placeholder="email@example.com"
              className={`w-full ${error ? 'border-red-300' : ''}`}
              onKeyDown={(e) => {
                if (e.key === 'Enter') handleInvite()
              }}
            />
            {error && (
              <div className="mt-2 flex items-center gap-1 text-sm text-red-600">
                <AlertCircle className="h-4 w-4" />
                <p>{error}</p>
              </div>
            )}
          </div>
          <div className="flex gap-2">
            <Button
              variant="outline"
              onClick={() => {
                setShowInviteDialog(false)
                setEmail('')
                setError(null)
              }}
              className="flex-1"
              disabled={inviteToGroup.isPending}
            >
              Отмена
            </Button>
            <Button
              onClick={handleInvite}
              disabled={inviteToGroup.isPending}
              className="flex-1 bg-blue-600 text-white hover:bg-blue-700"
            >
              {inviteToGroup.isPending ? 'Отправка...' : 'Пригласить'}
            </Button>
          </div>
        </div>
      </Dialog>

      <PremiumDialog
        isOpen={showPremiumDialog}
        onClose={() => setShowPremiumDialog(false)}
        reason="members"
      />
    </>
  )
}
