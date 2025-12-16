import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useGetAccounts, useGetBalance, useCreateAccount } from '@entities/account'
import type { Account } from '@entities/account'
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  LoadingSpinner,
  Button,
  Skeleton,
} from '@shared/ui'
import { formatCurrency } from '@shared/lib/utils'
import { BANK_NAMES, AVAILABLE_BANKS } from '@shared/config'
import { Building2 } from 'lucide-react'

function AccountCardSkeleton() {
  return (
    <Card>
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <Skeleton className="h-5 w-32" />
          <Skeleton className="h-4 w-24" />
        </div>
      </CardHeader>
      <CardContent>
        <Skeleton className="h-8 w-40" />
      </CardContent>
    </Card>
  )
}

function AccountCard({ account }: { account: Account }) {
  const navigate = useNavigate()
  const { data: balance, isLoading } = useGetBalance(account.accountId, account.clientId)

  const bankName = BANK_NAMES[account.clientId as keyof typeof BANK_NAMES] || account.clientName

  // Get bank color for left border
  const bank = AVAILABLE_BANKS.find((b) => b.id === account.clientId)
  const borderColor = bank
    ? bank.id === 1
      ? '#3b82f6'
      : bank.id === 2
        ? '#22c55e'
        : '#ef4444'
    : '#d1d5db'

  return (
    <Card
      className="cursor-pointer transition-all hover:shadow-md"
      style={{ borderLeft: `6px solid ${borderColor}` }}
      onClick={() =>
        navigate(
          `/accounts/${account.accountId}?clientId=${account.clientId}&name=${encodeURIComponent(account.accountName)}`
        )
      }
    >
      <CardHeader className="pb-3">
        <CardTitle className="flex items-center justify-between text-base">
          <span className="text-gray-900">{account.accountName}</span>
          <span className="text-sm font-normal text-gray-600">{bankName}</span>
        </CardTitle>
      </CardHeader>
      <CardContent>
        {isLoading ? (
          <LoadingSpinner size="sm" />
        ) : balance ? (
          <p className="text-2xl font-bold text-blue-600">
            {formatCurrency(balance.amount, balance.currency)}
          </p>
        ) : (
          <p className="text-sm text-gray-600">Нет данных</p>
        )}
      </CardContent>
    </Card>
  )
}

export function AccountList() {
  const { data: accounts, isLoading } = useGetAccounts()
  const { mutate: createAccount, isPending: isCreating } = useCreateAccount()
  const [selectedBankId, setSelectedBankId] = useState<number | null>(null)
  const [showAddBank, setShowAddBank] = useState(false)

  const handleConnectBank = (bankId: number) => {
    setSelectedBankId(bankId)
    createAccount(
      { client_id: bankId },
      {
        onSuccess: () => {
          setSelectedBankId(null)
          setShowAddBank(false)
        },
        onError: (error) => {
          console.error('Ошибка подключения банка:', error)
          setSelectedBankId(null)
        },
      }
    )
  }

  // Get list of connected bank IDs
  const connectedBankIds = new Set(accounts?.map((account) => account.clientId) || [])

  // Filter out already connected banks
  const availableBanksToConnect = AVAILABLE_BANKS.filter((bank) => !connectedBankIds.has(bank.id))

  if (isLoading) {
    return (
      <div className="grid gap-4">
        <AccountCardSkeleton />
        <AccountCardSkeleton />
        <AccountCardSkeleton />
      </div>
    )
  }

  if (!accounts?.length) {
    return (
      <div className="py-8">
        <div className="mb-6 text-center">
          <Building2 className="mx-auto mb-3 h-12 w-12 text-gray-400" />
          <h3 className="mb-2 text-lg font-semibold text-gray-900">Подключите свой первый банк</h3>
          <p className="text-sm text-gray-600">Выберите банк для подключения счетов</p>
        </div>

        <div className="grid gap-4">
          {availableBanksToConnect.map((bank) => (
            <Button
              key={bank.id}
              onClick={() => handleConnectBank(bank.id)}
              disabled={isCreating}
              className={`bg-gradient-to-r ${bank.color} h-auto w-full justify-start rounded-xl p-5 text-white shadow-lg transition-all hover:scale-[1.02] hover:shadow-xl disabled:opacity-50`}
            >
              {selectedBankId === bank.id ? (
                <>
                  <LoadingSpinner size="sm" className="mr-3" />
                  <span>Подключение {bank.displayName}...</span>
                </>
              ) : (
                <>
                  <Building2 className="mr-3 h-5 w-5" />
                  <div className="text-left">
                    <div className="font-semibold">{bank.displayName}</div>
                    <div className="text-xs opacity-90">Нажмите для подключения</div>
                  </div>
                </>
              )}
            </Button>
          ))}
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="grid gap-4">
        {accounts.map((account) => (
          <AccountCard key={`${account.clientId}-${account.accountId}`} account={account} />
        ))}
      </div>

      {/* Add More Banks Section - only show if there are banks left to connect */}
      {availableBanksToConnect.length > 0 && (
        <div className="pt-4">
          {!showAddBank ? (
            <Button
              variant="outline"
              onClick={() => setShowAddBank(true)}
              className="w-full border-dashed border-gray-300 text-gray-600 hover:border-blue-600 hover:text-blue-600"
            >
              <Building2 className="mr-2 h-4 w-4" />
              Добавить банк
            </Button>
          ) : (
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <h3 className="text-sm font-semibold text-gray-900">Выберите банк</h3>
                <button
                  onClick={() => setShowAddBank(false)}
                  className="text-sm text-gray-500 hover:text-gray-700"
                >
                  Свернуть
                </button>
              </div>
              <div className="grid gap-3">
                {availableBanksToConnect.map((bank) => (
                  <Button
                    key={bank.id}
                    onClick={() => handleConnectBank(bank.id)}
                    disabled={isCreating}
                    className={`bg-gradient-to-r ${bank.color} h-auto w-full justify-start rounded-xl p-4 text-white shadow-lg transition-all hover:scale-[1.02] hover:shadow-xl disabled:opacity-50`}
                  >
                    {selectedBankId === bank.id ? (
                      <>
                        <LoadingSpinner size="sm" className="mr-3" />
                        <span>Подключение {bank.displayName}...</span>
                      </>
                    ) : (
                      <>
                        <Building2 className="mr-3 h-5 w-5" />
                        <div className="text-left">
                          <div className="font-semibold">{bank.displayName}</div>
                          <div className="text-xs opacity-90">Нажмите для подключения</div>
                        </div>
                      </>
                    )}
                  </Button>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
