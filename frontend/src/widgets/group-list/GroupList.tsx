import { useNavigate } from 'react-router-dom'
import { useGetGroups } from '@entities/group'
import { Card, CardContent } from '@shared/ui'
import { Users, ChevronRight } from 'lucide-react'
import { ROUTES } from '@shared/config'

export function GroupList() {
  const navigate = useNavigate()
  const { data: groups, isLoading } = useGetGroups()

  if (isLoading) {
    return null
  }

  return (
    <div className="space-y-3">
      {groups && groups.length > 0 ? (
        <div className="space-y-2">
          {groups.map((group) => (
            <Card
              key={group.id}
              className="cursor-pointer transition-all hover:shadow-md"
              onClick={() => navigate(`${ROUTES.GROUPS}/${group.id}`)}
            >
              <CardContent className="p-4">
                <div className="flex items-center justify-between">
                  <p className="font-medium text-gray-900">{group.name}</p>
                  <ChevronRight className="h-5 w-5 text-gray-400" />
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      ) : (
        <div className="py-12 text-center">
          <Users className="mx-auto mb-3 h-12 w-12 text-gray-400" />
          <p className="mb-1 text-sm font-medium text-gray-900">Нет групп</p>
          <p className="text-xs text-gray-500">Создайте группу для совместного доступа к счетам</p>
        </div>
      )}
    </div>
  )
}
