import { z } from 'zod'

export const signInSchema = z.object({
  email: z.string().min(1, 'Email обязателен').email('Некорректный email'),
  password: z.string().min(1, 'Пароль обязателен'),
})

export type SignInFormData = z.infer<typeof signInSchema>
