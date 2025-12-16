import { Home, CreditCard, Users, User, ArrowRightLeft } from 'lucide-react'
import { useLocation, Link } from 'react-router-dom'
import { cn } from '@shared/lib/utils'
import { ROUTES } from '@shared/config'
import { useGetInvitations } from '@entities/group'

const navItems = [
  { path: ROUTES.DASHBOARD, icon: Home, label: 'Главная' },
  { path: ROUTES.ACCOUNTS, icon: CreditCard, label: 'Счета' },
  { path: '/payments', icon: ArrowRightLeft, label: 'Платежи' },
  { path: ROUTES.GROUPS, icon: Users, label: 'Группы' },
  { path: ROUTES.PROFILE, icon: User, label: 'Профиль' },
]

export function BottomNavigation() {
  const location = useLocation()
  const { data: invitations } = useGetInvitations()
  const pendingInvitationsCount = invitations?.filter((inv) => inv.status === 'pending').length || 0

  return (
    <nav className="fixed right-0 bottom-0 left-0 z-50 border-t border-gray-200 bg-white shadow-lg safe-area-pb">
      <div className="grid grid-cols-5 gap-0.5 sm:gap-1 p-1.5 sm:p-2">
        {navItems.map((item) => {
          const isActive =
            location.pathname === item.path ||
            (item.path === ROUTES.GROUPS && location.pathname.startsWith(ROUTES.GROUPS))
          const Icon = item.icon
          const showBadge = item.path === ROUTES.GROUPS && pendingInvitationsCount > 0

          return (
            <Link
              key={item.path}
              to={item.path}
              className={cn(
                'flex flex-col items-center justify-center gap-0.5 sm:gap-1 rounded-lg p-1.5 sm:p-2 text-[10px] sm:text-xs transition-all active:scale-95',
                isActive ? 'bg-blue-600 text-white' : 'text-gray-600 hover:bg-gray-100'
              )}
            >
              <div className="relative">
                <Icon className={cn('h-4 w-4 sm:h-5 sm:w-5', isActive && 'scale-110')} />
                {showBadge && (
                  <span className="absolute -top-1.5 -right-1.5 sm:-top-2 sm:-right-2 flex h-3.5 w-3.5 sm:h-4 sm:w-4 items-center justify-center rounded-full bg-red-500 text-[8px] sm:text-[10px] font-bold text-white">
                    {pendingInvitationsCount}
                  </span>
                )}
              </div>
              <span className="font-medium leading-tight truncate max-w-[60px]">{item.label}</span>
            </Link>
          )
        })}
      </div>
    </nav>
  )
}
