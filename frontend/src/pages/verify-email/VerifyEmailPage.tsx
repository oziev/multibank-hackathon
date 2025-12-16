import { useLocation, Navigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import { OtpForm } from '@features/auth/verify-email'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@shared/ui'
import { ROUTES } from '@shared/config'

export function VerifyEmailPage() {
  const location = useLocation()
  const email = location.state?.email

  if (!email) {
    return <Navigate to={ROUTES.SIGN_UP} replace />
  }

  return (
    <div className="flex min-h-screen items-center justify-center p-4">
      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.5 }}
        className="w-full max-w-md"
      >
        <Card>
          <CardHeader>
            <CardTitle className="text-2xl">Подтверждение email</CardTitle>
            <CardDescription>Введите код, отправленный на вашу почту</CardDescription>
          </CardHeader>
          <CardContent>
            <OtpForm email={email} />
          </CardContent>
        </Card>
      </motion.div>
    </div>
  )
}
