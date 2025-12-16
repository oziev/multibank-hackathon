import { z } from 'zod'

export const verifyEmailSchema = z.object({
  otpCode: z
    .string()
    .length(6, 'Код должен быть 6 символов')
    .regex(/^\d+$/, 'Код должен содержать только цифры'),
})

export type VerifyEmailFormData = z.infer<typeof verifyEmailSchema>
