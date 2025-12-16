import { createBrowserRouter, Navigate } from 'react-router-dom'
import { HomePage } from '@pages/home'
import { SignInPage } from '@pages/sign-in'
import { SignUpPage } from '@pages/sign-up'
import { VerifyEmailPage } from '@pages/verify-email'
import { DashboardPage } from '@pages/dashboard'
import { AccountsPage } from '@pages/accounts'
import { AccountDetailPage } from '@pages/account-detail'
import { GroupsPage } from '@pages/groups'
import { GroupDetailPage } from '@pages/group-detail'
import { GroupTransactionsPage } from '@pages/group-transactions'
import { ProfilePage } from '@pages/profile'
import { PremiumPage } from '@pages/premium'
import { AnalyticsPage } from '@pages/analytics'
import { PaymentsPage } from '@pages/payments'
import { LoyaltyCardsPage } from '@pages/loyalty-cards'
import { QRScannerPage } from '@pages/qr-scanner'
import { ReferralsPage } from '@pages/referrals'
import { TransactionsPage } from '@pages/transactions'
import { ROUTES } from '@shared/config'

// Временная заглушка для страницы кешбека
const CashbackPage = () => {
  return (
    <div className="min-h-screen bg-gray-50 pb-20 flex items-center justify-center">
      <div className="text-center">
        <h2 className="text-2xl font-bold text-gray-900 mb-4">Кешбек</h2>
        <p className="text-gray-600">Страница в разработке</p>
      </div>
    </div>
  )
}

export const router = createBrowserRouter([
  {
    path: ROUTES.HOME,
    element: <HomePage />,
  },
  {
    path: ROUTES.SIGN_IN,
    element: <SignInPage />,
  },
  {
    path: ROUTES.SIGN_UP,
    element: <SignUpPage />,
  },
  {
    path: ROUTES.VERIFY_EMAIL,
    element: <VerifyEmailPage />,
  },
  {
    path: ROUTES.DASHBOARD,
    element: <DashboardPage />,
    // TODO: Add ProtectedRoute wrapper in future
  },
  {
    path: ROUTES.ACCOUNTS,
    element: <AccountsPage />,
  },
  {
    path: '/accounts/:id',
    element: <AccountDetailPage />,
  },
  {
    path: ROUTES.GROUPS,
    element: <GroupsPage />,
  },
  {
    path: `${ROUTES.GROUPS}/:id`,
    element: <GroupDetailPage />,
  },
  {
    path: `${ROUTES.GROUPS}/:id/transactions`,
    element: <GroupTransactionsPage />,
  },
  {
    path: ROUTES.PROFILE,
    element: <ProfilePage />,
  },
  {
    path: ROUTES.PREMIUM,
    element: <PremiumPage />,
  },
  {
    path: '/analytics',
    element: <AnalyticsPage />,
  },
  {
    path: '/payments',
    element: <PaymentsPage />,
  },
  {
    path: '/loyalty-cards',
    element: <LoyaltyCardsPage />,
  },
  {
    path: '/qr-scanner',
    element: <QRScannerPage />,
  },
  {
    path: ROUTES.REFERRALS,
    element: <ReferralsPage />,
  },
  {
    path: ROUTES.CASHBACK,
    element: <CashbackPage />,
  },
  {
    path: '/transactions',
    element: <TransactionsPage />,
  },
  {
    path: '*',
    element: <Navigate to={ROUTES.HOME} replace />,
  },
])
