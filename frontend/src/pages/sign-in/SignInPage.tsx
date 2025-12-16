import { motion } from 'framer-motion'
import { SignInForm } from '@features/auth/sign-in'

export function SignInPage() {
  return (
    <div className="min-h-screen bg-gray-50">
      <div className="container mx-auto max-w-md px-6 pt-12 pb-6">
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
          className="mb-8"
        >
          <h1 className="mb-2 text-3xl font-bold text-gray-900">Вход</h1>
          <p className="text-gray-600">Войдите в свой аккаунт</p>
        </motion.div>
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2, duration: 0.5 }}
        >
          <SignInForm />
        </motion.div>
      </div>
    </div>
  )
}
