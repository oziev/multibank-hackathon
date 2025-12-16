import { useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import { Button } from '@shared/ui'
import { ROUTES } from '@shared/config'

export function HomePage() {
  const navigate = useNavigate()

  return (
    <div 
      className="flex min-h-screen items-center justify-center p-4 text-white"
      style={{ background: 'linear-gradient(135deg, #8B5CF6 0%, #3B82F6 40%, #06B6D4 100%)' }}
    >
      <div className="max-w-md text-center">
        <motion.h1
          initial={{ opacity: 0, y: -50 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8 }}
          className="mb-4 text-6xl font-extrabold"
          style={{ textShadow: '0 4px 20px rgba(0, 0, 0, 0.2)' }}
        >
          Банк Агрегатор
        </motion.h1>
        <motion.p
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.3, duration: 0.6 }}
          className="mb-10 text-xl font-medium"
          style={{ opacity: 0.95 }}
        >
          Управляй всеми своими счетами в одном месте
        </motion.p>

        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: 0.5, duration: 0.5 }}
          className="flex flex-col gap-4"
        >
          <button
            className="w-full rounded-2xl px-8 py-4 text-lg font-bold transition-all hover:scale-105 active:scale-95"
            style={{
              background: 'white',
              color: '#8B5CF6',
              boxShadow: '0 8px 24px rgba(255, 255, 255, 0.3)'
            }}
            onClick={() => navigate(ROUTES.SIGN_IN)}
          >
            Войти
          </button>
          <button
            className="w-full rounded-2xl px-8 py-4 text-lg font-bold text-white transition-all hover:scale-105 active:scale-95"
            style={{
              background: 'rgba(255, 255, 255, 0.15)',
              border: '2px solid rgba(255, 255, 255, 0.4)',
              boxShadow: '0 8px 24px rgba(0, 0, 0, 0.1)',
              backdropFilter: 'blur(10px)'
            }}
            onClick={() => navigate(ROUTES.SIGN_UP)}
          >
            Регистрация
          </button>
        </motion.div>
      </div>
    </div>
  )
}
