import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { useNavigate } from 'react-router-dom'
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
import { verifyEmailSchema, type VerifyEmailFormData } from '../model/schema'
import { useVerifyEmail } from '../api/verifyEmail'

interface OtpFormProps {
  email: string
}

export function OtpForm({ email }: OtpFormProps) {
  const navigate = useNavigate()
  const { mutate: verify, isPending } = useVerifyEmail()

  const form = useForm<VerifyEmailFormData>({
    resolver: zodResolver(verifyEmailSchema),
    defaultValues: {
      otpCode: '',
    },
  })

  const onSubmit = (data: VerifyEmailFormData) => {
    verify(
      { email, otpCode: data.otpCode },
      {
        onSuccess: () => {
          // TODO: Show success animation
          navigate(ROUTES.DASHBOARD)
        },
        onError: (error) => {
          console.error('Verification error:', error)
          // TODO: Show toast notification
        },
      }
    )
  }

  return (
    <Form {...form}>
      <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
        <FormField
          control={form.control}
          name="otpCode"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Код подтверждения</FormLabel>
              <FormControl>
                <Input
                  type="text"
                  inputMode="numeric"
                  maxLength={6}
                  placeholder="000000"
                  className="text-center text-2xl tracking-widest"
                  {...field}
                />
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />

        <Button type="submit" className="w-full" size="lg" disabled={isPending}>
          {isPending ? 'Проверка...' : 'Подтвердить'}
        </Button>

        <p className="text-muted-foreground text-center text-sm">
          Код отправлен на <span className="font-medium">{email}</span>
        </p>
      </form>
    </Form>
  )
}
