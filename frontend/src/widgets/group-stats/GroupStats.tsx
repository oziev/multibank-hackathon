import { useGetGroupAccounts, useGetGroupBalance } from '@entities/group'
import { Card, CardContent, Skeleton } from '@shared/ui'
import { Wallet, Users, CreditCard } from 'lucide-react'
import { formatCurrency } from '@shared/lib/utils'

type GroupStatsProps = {
  groupId: number
}

export function GroupStats({ groupId }: GroupStatsProps) {
  const { data: accounts, isLoading } = useGetGroupAccounts(groupId)
  const { data: totalBalance } = useGetGroupBalance(groupId)

  // Get unique members count from account owners
  const uniqueMembers = accounts ? [...new Set(accounts.map((acc) => acc.owner.name))].length : 0

  if (isLoading) {
    return (
      <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
        <Skeleton className="h-20" />
        <Skeleton className="h-20" />
        <Skeleton className="h-20" />
      </div>
    )
  }

  const stats = [
    {
      icon: Wallet,
      label: 'Общий баланс',
      value: totalBalance ? formatCurrency(totalBalance.amount, totalBalance.currency) : '0 ₽',
      color: 'from-blue-500 to-cyan-500',
      bgColor: 'bg-blue-50',
      iconColor: 'text-blue-600',
    },
    {
      icon: Users,
      label: 'Участников',
      value: uniqueMembers,
      color: 'from-purple-500 to-pink-500',
      bgColor: 'bg-purple-50',
      iconColor: 'text-purple-600',
    },
    {
      icon: CreditCard,
      label: 'Счетов',
      value: accounts?.length || 0,
      color: 'from-green-500 to-emerald-500',
      bgColor: 'bg-green-50',
      iconColor: 'text-green-600',
    },
  ]

  return (
    <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
      {stats.map((stat, index) => {
        const Icon = stat.icon
        return (
          <Card key={index} className="overflow-hidden">
            <CardContent className="p-4">
              <div className="flex items-center gap-3">
                <div
                  className={`flex h-12 w-12 items-center justify-center rounded-xl ${stat.bgColor}`}
                >
                  <Icon className={`h-6 w-6 ${stat.iconColor}`} />
                </div>
                <div className="flex-1">
                  <p className="text-xs font-medium text-gray-500">{stat.label}</p>
                  <p className="text-xl font-bold text-gray-900">{stat.value}</p>
                </div>
              </div>
            </CardContent>
          </Card>
        )
      })}
    </div>
  )
}
