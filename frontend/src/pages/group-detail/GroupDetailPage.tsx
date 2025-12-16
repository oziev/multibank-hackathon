import { useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import { MobileHeader } from '@widgets/header'
import { BottomNavigation } from '@widgets/bottom-navigation'
import { GroupStats } from '@widgets/group-stats'
import { GroupMembers } from '@widgets/group-members'
import { GroupAccounts } from '@widgets/group-accounts'
import { GroupTransactions } from '@widgets/group-transactions'
import { useGetGroups, useDeleteGroup, useExitGroup } from '@entities/group'
import { useGetMe } from '@entities/user'
import { Button, Dialog } from '@shared/ui'
import { ArrowLeft, Trash2, LogOut } from 'lucide-react'
import { ROUTES } from '@shared/config'

export function GroupDetailPage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const groupId = parseInt(id || '0', 10)

  const { data: groups } = useGetGroups()
  const { data: user } = useGetMe()
  const deleteGroup = useDeleteGroup()
  const exitGroup = useExitGroup()

  const [showDeleteDialog, setShowDeleteDialog] = useState(false)
  const [showExitDialog, setShowExitDialog] = useState(false)

  const group = groups?.find((g) => g.id === groupId)

  if (!group || !user) {
    return (
      <div className="min-h-screen bg-gray-50 pb-20">
        <MobileHeader />
        <main className="container mx-auto px-4 py-6">
          <p className="text-center text-gray-500">Группа не найдена</p>
        </main>
        <BottomNavigation />
      </div>
    )
  }

  const isOwner = group.ownerId === user.id

  const handleDelete = () => {
    deleteGroup.mutate(groupId, {
      onSuccess: () => {
        setShowDeleteDialog(false)
        navigate(ROUTES.GROUPS)
      },
    })
  }

  const handleExit = () => {
    exitGroup.mutate(groupId, {
      onSuccess: () => {
        setShowExitDialog(false)
        navigate(ROUTES.GROUPS)
      },
    })
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
            onClick={() => navigate(ROUTES.GROUPS)}
            className="mb-4 flex items-center gap-2 text-sm text-gray-600 hover:text-gray-900"
          >
            <ArrowLeft className="h-4 w-4" />
            Назад к группам
          </button>

          <div className="flex items-center justify-between">
            <h2 className="text-2xl font-bold text-gray-900">{group.name}</h2>
            <GroupMembers groupId={groupId} ownerId={group.ownerId} currentUserId={user.id} />
          </div>
        </motion.div>

        {/* Stats */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1, duration: 0.5 }}
          className="mb-6"
        >
          <GroupStats groupId={groupId} />
        </motion.div>

        {/* Accounts */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2, duration: 0.5 }}
          className="mb-6"
        >
          <GroupAccounts groupId={groupId} />
        </motion.div>

        {/* Transactions */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3, duration: 0.5 }}
          className="mb-6"
        >
          <GroupTransactions groupId={groupId} />
        </motion.div>

        {/* Actions */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4, duration: 0.5 }}
          className="space-y-3"
        >
          {isOwner ? (
            <Button
              variant="outline"
              onClick={() => setShowDeleteDialog(true)}
              className="w-full border-red-300 text-red-600 hover:bg-red-50"
            >
              <Trash2 className="mr-2 h-4 w-4" />
              Удалить группу
            </Button>
          ) : (
            <Button
              variant="outline"
              onClick={() => setShowExitDialog(true)}
              className="w-full border-orange-300 text-orange-600 hover:bg-orange-50"
            >
              <LogOut className="mr-2 h-4 w-4" />
              Выйти из группы
            </Button>
          )}
        </motion.div>
      </main>

      <BottomNavigation />

      {/* Delete Dialog */}
      <Dialog
        isOpen={showDeleteDialog}
        onClose={() => setShowDeleteDialog(false)}
        title="Удалить группу?"
        description="Это действие нельзя отменить. Все участники потеряют доступ к группе."
        onConfirm={handleDelete}
        confirmText="Удалить"
        confirmVariant="destructive"
        isLoading={deleteGroup.isPending}
      />

      {/* Exit Dialog */}
      <Dialog
        isOpen={showExitDialog}
        onClose={() => setShowExitDialog(false)}
        title="Выйти из группы?"
        description="Вы потеряете доступ к счетам этой группы. Владелец сможет пригласить вас снова."
        onConfirm={handleExit}
        confirmText="Выйти"
        confirmVariant="destructive"
        isLoading={exitGroup.isPending}
      />
    </div>
  )
}
