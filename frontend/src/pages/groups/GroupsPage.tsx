import { useState } from 'react'
import { motion } from 'framer-motion'
import { MobileHeader } from '@widgets/header'
import { BottomNavigation } from '@widgets/bottom-navigation'
import { InvitationsList } from '@widgets/invitations-list'
import { GroupList } from '@widgets/group-list'
import { useGetGroups, useGetGroupSettings, useCreateGroup } from '@entities/group'
import { useGetMe } from '@entities/user'
import { Button, Input, Card, CardContent, PremiumDialog } from '@shared/ui'
import { Plus } from 'lucide-react'

export function GroupsPage() {
  const { data: groups } = useGetGroups()
  const { data: settings } = useGetGroupSettings()
  const { data: user } = useGetMe()
  const createGroup = useCreateGroup()

  const [showCreateForm, setShowCreateForm] = useState(false)
  const [groupName, setGroupName] = useState('')
  const [showPremiumDialog, setShowPremiumDialog] = useState(false)

  // Count only groups where current user is owner
  const myGroupsCount = groups?.filter((g) => g.ownerId === user?.id).length || 0
  const canCreateMore = !settings || myGroupsCount < settings.maxGroups

  const handleCreateClick = () => {
    if (!canCreateMore) {
      setShowPremiumDialog(true)
    } else {
      setShowCreateForm(true)
    }
  }

  const handleCreateGroup = () => {
    if (!groupName.trim()) {
      alert('❌ Укажите название группы')
      return
    }

    if (groupName.trim().length < 3) {
      alert('❌ Название должно содержать минимум 3 символа')
      return
    }

    if (groupName.trim().length > 50) {
      alert('❌ Название не может быть длиннее 50 символов')
      return
    }

    createGroup.mutate(
      { name: groupName.trim() },
      {
        onSuccess: () => {
          alert(`✅ Группа "${groupName.trim()}" создана!`)
          setGroupName('')
          setShowCreateForm(false)
        },
        onError: (error: any) => {
          alert(`❌ Ошибка создания группы\n\n${error?.message || 'Попробуйте позже'}`)
        }
      }
    )
  }

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
          <div className="flex items-center justify-between">
            <div>
              <h2 className="mb-2 text-2xl font-bold text-gray-900">Группы</h2>
              <p className="text-gray-600">Совместный доступ к счетам</p>
            </div>
            <Button
              size="sm"
              onClick={handleCreateClick}
              className="bg-blue-600 text-white hover:bg-blue-700"
            >
              <Plus className="h-4 w-4" />
            </Button>
          </div>

          {showCreateForm && (
            <Card className="mt-4 border-blue-200">
              <CardContent className="p-4">
                <div className="space-y-3">
                  <div>
                    <label className="mb-1 block text-sm font-medium text-gray-900">
                      Название группы
                    </label>
                    <Input
                      value={groupName}
                      onChange={(e) => setGroupName(e.target.value)}
                      placeholder="Например: Семейный бюджет"
                      className="w-full"
                      autoFocus
                      onKeyDown={(e) => {
                        if (e.key === 'Enter') handleCreateGroup()
                        if (e.key === 'Escape') {
                          setShowCreateForm(false)
                          setGroupName('')
                        }
                      }}
                    />
                  </div>
                  <div className="flex gap-2">
                    <Button
                      variant="outline"
                      onClick={() => {
                        setShowCreateForm(false)
                        setGroupName('')
                      }}
                      className="flex-1"
                    >
                      Отмена
                    </Button>
                    <Button
                      onClick={handleCreateGroup}
                      disabled={!groupName.trim() || createGroup.isPending}
                      className="flex-1 bg-blue-600 text-white hover:bg-blue-700"
                    >
                      {createGroup.isPending ? 'Создание...' : 'Создать'}
                    </Button>
                  </div>
                </div>
              </CardContent>
            </Card>
          )}
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1, duration: 0.5 }}
          className="space-y-6"
        >
          {/* Invitations */}
          <InvitationsList />

          {/* Groups List */}
          <GroupList />
        </motion.div>
      </main>

      <BottomNavigation />

      <PremiumDialog
        isOpen={showPremiumDialog}
        onClose={() => setShowPremiumDialog(false)}
        reason="groups"
      />
    </div>
  )
}
