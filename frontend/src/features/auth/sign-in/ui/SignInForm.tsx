import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { useNavigate, Link } from 'react-router-dom'
import { LogIn, Eye, EyeOff } from 'lucide-react'
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
  Button,
  Input,
} from '@shared/ui'
import { ROUTES } from '@shared/config'
import { signInSchema, type SignInFormData } from '../model/schema'
import { useSignIn } from '../api/signIn'
import { ApiError } from '@shared/api'

export function SignInForm() {
  const navigate = useNavigate()
  const { mutate: signIn, isPending } = useSignIn()
  const [error, setError] = useState<string | null>(null)
  const [showPassword, setShowPassword] = useState(false)

  const form = useForm<SignInFormData>({
    resolver: zodResolver(signInSchema),
    defaultValues: {
      email: '',
      password: '',
    },
  })

  const onSubmit = (data: SignInFormData) => {
    setError(null)
    signIn(data, {
      onSuccess: () => {
        navigate(ROUTES.DASHBOARD)
      },
      onError: (error) => {
        if (error instanceof ApiError) {
          setError(error.message)
        } else {
          setError('Произошла ошибка при входе. Попробуйте снова.')
        }
      },
    })
  }

  return (
    <div className="space-y-6">
      <Form {...form}>
        <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
          {error && (
            <div className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-800">
              {error}
            </div>
          )}

          <FormField
            control={form.control}
            name="email"
            render={({ field }) => (
              <FormItem>
                <FormLabel>Email</FormLabel>
                <FormControl>
                  <Input
                    type="email"
                    placeholder="ivan@example.com"
                    autoComplete="email"
                    {...field}
                  />
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />

          <FormField
            control={form.control}
            name="password"
            render={({ field }) => (
              <FormItem>
                <FormLabel>Пароль</FormLabel>
                <FormControl>
                  <div className="relative">
                    <Input
                      type={showPassword ? 'text' : 'password'}
                      placeholder="••••••••"
                      autoComplete="current-password"
                      className="pr-10"
                      {...field}
                    />
                    <button
                      type="button"
                      onClick={() => setShowPassword(!showPassword)}
                      className="absolute top-1/2 right-3 -translate-y-1/2 text-gray-500 hover:text-gray-700"
                    >
                      {showPassword ? <EyeOff className="h-5 w-5" /> : <Eye className="h-5 w-5" />}
                    </button>
                  </div>
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />

          <Button
            type="submit"
            className="w-full bg-blue-600 font-semibold text-white shadow-lg transition-all duration-200 hover:bg-blue-700 hover:shadow-xl"
            size="lg"
            disabled={isPending}
          >
            {isPending ? (
              <>
                <span className="animate-pulse">Вход...</span>
              </>
            ) : (
              <>
                <LogIn className="mr-2 h-5 w-5" />
                Войти
              </>
            )}
          </Button>
        </form>
      </Form>

      <p className="text-muted-foreground text-center text-sm">
        Нет аккаунта?{' '}
        <Link to={ROUTES.SIGN_UP} className="text-primary font-medium hover:underline">
          Зарегистрироваться
        </Link>
      </p>
    </div>
  )
}
