import { useNavigate } from 'react-router-dom'
import { Button } from '@shared/ui'
import { ROUTES } from '@shared/config'
import { useLogout } from '../api/logout'

interface LogoutButtonProps {
  variant?: 'default' | 'ghost' | 'outline'
}

export function LogoutButton({ variant = 'ghost' }: LogoutButtonProps) {
  const navigate = useNavigate()
  const { mutate: logout, isPending } = useLogout()

  const handleLogout = () => {
    logout(undefined, {
      onSuccess: () => {
        navigate(ROUTES.HOME)
      },
      onError: (error) => {
        console.error('Logout error:', error)
      },
    })
  }

  return (
    <Button
      variant={variant}
      onClick={handleLogout}
      disabled={isPending}
      className={
        variant === 'ghost'
          ? 'text-gray-900 hover:bg-gray-100'
          : variant === 'outline'
            ? 'w-full border-red-500 text-red-600 hover:bg-red-50'
            : ''
      }
    >
      {isPending ? 'Выход...' : 'Выйти'}
    </Button>
  )
}
