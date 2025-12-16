import { Link } from 'react-router-dom'
import { motion } from 'framer-motion'
import { SignUpForm } from '@features/auth/sign-up'
import { ROUTES } from '@shared/config'

export function SignUpPage() {
  return (
    <div className="min-h-screen bg-gray-50">
      <div className="container mx-auto max-w-md px-6 pt-12 pb-6">
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
          className="mb-8"
        >
          <h1 className="mb-2 text-3xl font-bold text-gray-900">Регистрация</h1>
          <p className="text-gray-600">Создайте аккаунт для начала работы</p>
        </motion.div>
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2, duration: 0.5 }}
        >
          <SignUpForm />
        </motion.div>
        <motion.p
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.4, duration: 0.5 }}
          className="mt-6 text-center text-sm text-gray-600"
        >
          Уже есть аккаунт?{' '}
          <Link to={ROUTES.SIGN_IN} className="font-medium text-blue-600 hover:underline">
            Войти
          </Link>
        </motion.p>
      </div>
    </div>
  )
}
