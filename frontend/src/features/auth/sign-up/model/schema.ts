import { z } from 'zod'

export const signUpSchema = z
  .object({
    email: z.string().min(1, 'Email обязателен').email('Некорректный email'),
    phone: z.string()
      .min(1, 'Номер телефона обязателен')
      .regex(/^\+?[0-9]{10,15}$/, 'Некорректный номер телефона (10-15 цифр)'),
    password: z
      .string()
      .min(8, 'Пароль должен быть минимум 8 символов')
      .regex(/[a-z]/, 'Пароль должен содержать строчные буквы')
      .regex(/[A-Z]/, 'Пароль должен содержать заглавные буквы')
      .regex(/[0-9]/, 'Пароль должен содержать цифры'),
    confirmPassword: z.string().min(1, 'Подтвердите пароль'),
    name: z
      .string()
      .min(2, 'Имя должно быть минимум 2 символа')
      .max(50, 'Имя должно быть максимум 50 символов'),
    birthDate: z.string().refine((val) => {
      const date = new Date(val)
      const age = new Date().getFullYear() - date.getFullYear()
      return age >= 18
    }, 'Вам должно быть минимум 18 лет'),
  })
  .refine((data) => data.password === data.confirmPassword, {
    message: 'Пароли не совпадают',
    path: ['confirmPassword'],
  })

export type SignUpFormData = z.infer<typeof signUpSchema>
