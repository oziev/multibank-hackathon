import { useState, useRef, useEffect } from 'react'
import { motion } from 'framer-motion'
import { MobileHeader } from '@widgets/header'
import { BottomNavigation } from '@widgets/bottom-navigation'
import { Card, CardContent, Button, Input, Label } from '@shared/ui'
import { QrCode, Scan, ArrowLeft, X } from 'lucide-react'
import { useNavigate } from 'react-router-dom'
import { Html5Qrcode } from 'html5-qrcode'
import { QRCodeSVG } from 'qrcode.react'
import { useGetAccounts } from '@entities/account'
import { useGetMe } from '@entities/user'
import { apiClient } from '@shared/api'
import { useMutation, useQueryClient } from '@tanstack/react-query'

export function QRScannerPage() {
  const navigate = useNavigate()
  const [activeTab, setActiveTab] = useState<'scan' | 'generate'>('scan')
  const [amount, setAmount] = useState('')
  const [description, setDescription] = useState('')
  const [isScanning, setIsScanning] = useState(false)
  const [scannedData, setScannedData] = useState<string | null>(null)
  const [showPaymentModal, setShowPaymentModal] = useState(false)
  const [paymentAmount, setPaymentAmount] = useState('')
  const scannerRef = useRef<Html5Qrcode | null>(null)
  const scanAreaRef = useRef<HTMLDivElement>(null)
  const { data: accounts } = useGetAccounts()
  const { data: user } = useGetMe()
  const queryClient = useQueryClient()

  // Останавливаем сканирование при размонтировании
  useEffect(() => {
    return () => {
      if (scannerRef.current && isScanning) {
        scannerRef.current.stop().catch(() => {})
      }
    }
  }, [isScanning])

  const startScanning = async () => {
    // Останавливаем предыдущее сканирование если оно есть
    if (scannerRef.current) {
      try {
        await scannerRef.current.stop()
        await scannerRef.current.clear()
      } catch (e) {
        // Игнорируем ошибки при остановке
      }
      scannerRef.current = null
    }

    if (!scanAreaRef.current) return

    const elementId = 'qr-reader'
    const element = document.getElementById(elementId)
    if (!element) {
      alert('❌ Элемент для сканера не найден')
      return
    }

    try {
      const html5QrCode = new Html5Qrcode(elementId)
      scannerRef.current = html5QrCode

      // Пытаемся использовать заднюю камеру, если не получается - используем любую доступную
      let cameraConfig: any = { facingMode: 'environment' }
      
      try {
        await html5QrCode.start(
          cameraConfig,
          {
            fps: 10,
            qrbox: { width: 250, height: 250 },
            aspectRatio: 1.0,
          },
          (decodedText) => {
            // QR-код успешно отсканирован
            handleScannedQR(decodedText)
            stopScanning()
          },
          () => {
            // Игнорируем ошибки сканирования (они происходят постоянно пока не найден код)
          }
        )
        setIsScanning(true)
      } catch (cameraError: any) {
        // Если не удалось использовать заднюю камеру, пробуем любую доступную
        if (cameraError.message && cameraError.message.includes('environment')) {
          console.log('Задняя камера недоступна, пробуем любую доступную')
          cameraConfig = { facingMode: 'user' } // Передняя камера
          
          await html5QrCode.start(
            cameraConfig,
            {
              fps: 10,
              qrbox: { width: 250, height: 250 },
              aspectRatio: 1.0,
            },
            (decodedText) => {
              handleScannedQR(decodedText)
              stopScanning()
            },
            () => {
              // Игнорируем ошибки сканирования
            }
          )
          setIsScanning(true)
        } else {
          throw cameraError
        }
      }
    } catch (error: any) {
      console.error('Ошибка доступа к камере:', error)
      let errorMessage = 'Неизвестная ошибка'
      
      if (error.name === 'NotAllowedError' || error.message?.includes('Permission denied')) {
        errorMessage = 'Доступ к камере запрещен. Разрешите доступ к камере в настройках браузера.'
      } else if (error.name === 'NotFoundError' || error.message?.includes('not found')) {
        errorMessage = 'Камера не найдена. Убедитесь, что устройство имеет камеру.'
      } else if (error.name === 'NotReadableError' || error.message?.includes('not readable')) {
        errorMessage = 'Камера уже используется другим приложением. Закройте другие приложения, использующие камеру.'
      } else if (error.message) {
        errorMessage = error.message
      }
      
      alert(`❌ Ошибка доступа к камере: ${errorMessage}\n\nДетали: ${error.name || 'Unknown'}`)
      setIsScanning(false)
    }
  }

  const stopScanning = async () => {
    if (scannerRef.current) {
      try {
        const scanner = scannerRef.current
        scannerRef.current = null // Сбрасываем ссылку перед остановкой
        
        // Останавливаем сканирование
        await scanner.stop()
        
        // Очищаем DOM с задержкой, чтобы React успел обработать изменения
        setTimeout(async () => {
          try {
            await scanner.clear()
          } catch (clearError) {
            // Игнорируем ошибки очистки
            console.log('Ошибка очистки сканера (можно игнорировать):', clearError)
          }
        }, 100)
      } catch (error: any) {
        // Игнорируем ошибки при остановке (элемент может быть уже удален React)
        console.log('Ошибка остановки сканера (можно игнорировать):', error)
      }
    }
    setIsScanning(false)
  }

  const handleScannedQR = (data: string) => {
    setScannedData(data)
    
    // Парсим данные QR-кода
    // Формат может быть: phone:79001234567, card:1234567890123456, payment:amount:phone:79001234567, или просто номер телефона/карты
    let parsedData: { type: 'phone' | 'card' | 'unknown', value: string, amount?: number } = {
      type: 'unknown',
      value: data
    }

    // Проверяем формат payment:amount:phone:79001234567
    if (data.startsWith('payment:')) {
      const parts = data.replace('payment:', '').split(':')
      if (parts.length >= 2) {
        const amount = parseFloat(parts[0])
        if (!isNaN(amount)) {
          parsedData.amount = amount
          const identifier = parts.slice(1).join(':')
          
          if (identifier.startsWith('phone:')) {
            parsedData.type = 'phone'
            parsedData.value = identifier.replace('phone:', '').replace(/[^\d]/g, '')
          } else if (identifier.startsWith('card:')) {
            parsedData.type = 'card'
            parsedData.value = identifier.replace('card:', '').replace(/[^\d]/g, '')
          } else {
            // Пытаемся определить тип по формату
            const cleanIdentifier = identifier.replace(/[^\d]/g, '')
            if (/^\d{10,15}$/.test(cleanIdentifier)) {
              parsedData.type = 'phone'
              parsedData.value = cleanIdentifier
            } else if (/^\d{16,19}$/.test(cleanIdentifier)) {
              parsedData.type = 'card'
              parsedData.value = cleanIdentifier
            }
          }
        }
      }
    }
    // Проверяем формат phone:79001234567
    else if (data.startsWith('phone:')) {
      parsedData.type = 'phone'
      parsedData.value = data.replace('phone:', '').replace(/[^\d]/g, '')
    }
    // Проверяем формат card:1234567890123456
    else if (data.startsWith('card:')) {
      parsedData.type = 'card'
      parsedData.value = data.replace('card:', '').replace(/[^\d]/g, '')
    }
    // Проверяем, является ли это номером телефона (10-15 цифр после очистки)
    else {
      const cleanData = data.replace(/[^\d]/g, '')
      if (/^\d{10,15}$/.test(cleanData)) {
        parsedData.type = 'phone'
        parsedData.value = cleanData
      }
      // Проверяем, является ли это номером карты (16-19 цифр)
      else if (/^\d{16,19}$/.test(cleanData)) {
        parsedData.type = 'card'
        parsedData.value = cleanData
      }
    }

    // Если есть сумма и телефон, показываем модальное окно для подтверждения платежа
    if (parsedData.type === 'phone') {
      if (parsedData.amount) {
        setPaymentAmount(parsedData.amount.toString())
      } else {
        setPaymentAmount('')
      }
      setShowPaymentModal(true)
    } else {
      // Иначе показываем информацию о том, что было отсканировано
      const typeName = parsedData.type === 'card' ? 'Карта' : 'Неизвестно'
      const message = parsedData.type === 'card' ? 'Для перевода на карту перейдите в раздел "Платежи"' : 'Для оплаты перейдите в раздел "Платежи"'
      alert(`✅ QR-код отсканирован!\n\nТип: ${typeName}\nЗначение: ${parsedData.value}\n\n${message}`)
    }
  }

  const [isPaymentProcessing, setIsPaymentProcessing] = useState(false)

  const paymentMutation = useMutation({
    mutationFn: async (data: { fromAccountId: number, toPhone: string, amount: number, description?: string }) => {
      if (isPaymentProcessing) {
        throw new Error('Платеж уже обрабатывается, пожалуйста, подождите')
      }
      setIsPaymentProcessing(true)
      
      try {
        return apiClient.post('/api/payments/transfer-by-phone', {
          fromAccountId: data.fromAccountId,
          toPhone: data.toPhone,
          amount: data.amount,
          description: data.description || 'Оплата по QR-коду'
        })
      } finally {
        setIsPaymentProcessing(false)
      }
    },
    onSuccess: () => {
      setIsPaymentProcessing(false)
      queryClient.invalidateQueries({ queryKey: ['payments', 'history'] })
      queryClient.invalidateQueries({ queryKey: ['accounts'] })
      queryClient.invalidateQueries({ queryKey: ['transactions'] })
      setShowPaymentModal(false)
      setScannedData(null)
      alert('✅ Платеж успешно выполнен!')
    },
    onError: (error: any) => {
      setIsPaymentProcessing(false)
      alert(`❌ Ошибка: ${error?.message || 'Не удалось выполнить платеж'}`)
    }
  })

  const handleGenerateQR = () => {
    if (!amount || parseFloat(amount) <= 0) {
      alert('❌ Укажите сумму для получения')
      return
    }
    // QR-код будет сгенерирован автоматически через QRCodeSVG компонент
  }

  // Генерируем данные для QR-кода
  const userPhone = (user as any)?.phone || '79000000000'
  const qrData = amount && parseFloat(amount) > 0
    ? `payment:${amount}:phone:${String(userPhone).replace(/[^\d]/g, '')}`
    : ''

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-50 via-white to-blue-50 pb-20">
      <MobileHeader />

      <main className="container mx-auto px-4 py-6">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
        >
          <button
            onClick={async () => {
              if (isScanning) await stopScanning()
              navigate(-1)
            }}
            className="mb-4 flex items-center gap-2 text-sm text-gray-600 hover:text-gray-900"
          >
            <ArrowLeft className="h-4 w-4" />
            Назад
          </button>

          <h2 className="mb-2 text-2xl font-bold text-gray-900">QR Платежи</h2>
          <p className="text-gray-600">Оплата и получение денег по QR коду</p>
        </motion.div>

        {/* Tabs */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1, duration: 0.5 }}
          className="my-6"
        >
          <div className="flex gap-2 rounded-xl bg-white p-2 shadow-sm">
            <button
              onClick={async () => {
                if (isScanning) await stopScanning()
                setActiveTab('scan')
              }}
              className={`flex-1 rounded-lg px-4 py-3 text-sm font-medium transition-all ${
                activeTab === 'scan'
                  ? 'bg-gradient-to-r from-purple-600 to-blue-600 text-white shadow-lg'
                  : 'text-gray-600 hover:bg-gray-50'
              }`}
            >
              <Scan className="mx-auto mb-1 h-5 w-5" />
              Сканировать
            </button>
            <button
              onClick={async () => {
                if (isScanning) await stopScanning()
                setActiveTab('generate')
              }}
              className={`flex-1 rounded-lg px-4 py-3 text-sm font-medium transition-all ${
                activeTab === 'generate'
                  ? 'bg-gradient-to-r from-purple-600 to-blue-600 text-white shadow-lg'
                  : 'text-gray-600 hover:bg-gray-50'
              }`}
            >
              <QrCode className="mx-auto mb-1 h-5 w-5" />
              Получить
            </button>
          </div>
        </motion.div>

        {activeTab === 'scan' ? (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2, duration: 0.5 }}
          >
            <Card>
              <CardContent className="p-8">
                <div className="text-center">
                  <div
                    ref={scanAreaRef}
                    id="qr-reader"
                    className={`mx-auto mb-6 flex h-64 w-full items-center justify-center rounded-2xl border-4 border-dashed ${
                      isScanning
                        ? 'border-green-300 bg-green-50'
                        : 'border-purple-300 bg-purple-50'
                    }`}
                  >
                    {!isScanning && (
                      <Scan className="h-24 w-24 text-purple-400" />
                    )}
                  </div>
                  <h3 className="mb-2 text-lg font-semibold text-gray-900">
                    {isScanning ? 'Сканирование...' : 'Отсканируйте QR код'}
                  </h3>
                  <p className="mb-6 text-sm text-gray-600">
                    {isScanning
                      ? 'Наведите камеру на QR код'
                      : 'Наведите камеру на QR код для оплаты'}
                  </p>
                  {!isScanning ? (
                    <Button
                      className="w-full bg-gradient-to-r from-purple-600 to-blue-600"
                      onClick={startScanning}
                    >
                      <Scan className="mr-2 h-4 w-4" />
                      Открыть камеру
                    </Button>
                  ) : (
                    <Button
                      className="w-full bg-red-600 hover:bg-red-700"
                      onClick={stopScanning}
                    >
                      <X className="mr-2 h-4 w-4" />
                      Остановить сканирование
                    </Button>
                  )}
                </div>
              </CardContent>
            </Card>
          </motion.div>
        ) : (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2, duration: 0.5 }}
          >
            <Card>
              <CardContent className="p-6">
                <h3 className="mb-4 text-lg font-semibold text-gray-900">
                  Создать QR код для получения денег
                </h3>
                <div className="space-y-4">
                  <div>
                    <Label>Сумма для получения (₽)</Label>
                    <Input
                      type="number"
                      placeholder="1000"
                      value={amount}
                      onChange={(e) => setAmount(e.target.value)}
                    />
                  </div>
                  <div>
                    <Label>Описание (необязательно)</Label>
                    <Input
                      type="text"
                      placeholder="За что платеж"
                      value={description}
                      onChange={(e) => setDescription(e.target.value)}
                    />
                  </div>

                  {amount && parseFloat(amount) > 0 && qrData && (
                    <div className="mt-6 rounded-xl border-2 border-purple-200 bg-purple-50 p-6">
                      <div className="mx-auto mb-4 flex h-48 w-48 items-center justify-center rounded-xl bg-white p-4">
                        <QRCodeSVG value={qrData} size={192} level="H" />
                      </div>
                      <div className="text-center">
                        <p className="mb-1 text-2xl font-bold text-purple-600">
                          {amount} ₽
                        </p>
                        <p className="text-sm text-gray-600">{description || 'Без описания'}</p>
                      </div>
                    </div>
                  )}

                  <div className="flex gap-3 pt-2">
                    <Button
                      variant="outline"
                      onClick={() => navigate(-1)}
                      className="flex-1"
                    >
                      Отмена
                    </Button>
                    <Button
                      onClick={handleGenerateQR}
                      className="flex-1 bg-gradient-to-r from-purple-600 to-blue-600"
                    >
                      <QrCode className="mr-2 h-4 w-4" />
                      Сгенерировать
                    </Button>
                  </div>
                </div>
              </CardContent>
            </Card>
          </motion.div>
        )}

        {/* Инструкции */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3, duration: 0.5 }}
          className="mt-6"
        >
          <Card className="bg-gradient-to-r from-blue-50 to-purple-50">
            <CardContent className="p-4">
              <h4 className="mb-2 font-semibold text-gray-900">💡 Как это работает?</h4>
              <ul className="space-y-1 text-sm text-gray-700">
                <li>• <strong>Сканировать:</strong> Оплачивайте по QR коду в магазинах</li>
                <li>• <strong>Получить:</strong> Создайте QR для получения денег от друзей</li>
                <li>• <strong>Безопасно:</strong> Все платежи проходят через защищенное соединение</li>
              </ul>
            </CardContent>
          </Card>
        </motion.div>
      </main>

      {/* Модальное окно для оплаты по QR */}
      {showPaymentModal && scannedData && (
        <PaymentModal
          amount={paymentAmount}
          scannedData={scannedData}
          accounts={accounts || []}
          onClose={() => {
            setShowPaymentModal(false)
            setScannedData(null)
          }}
          onPay={(fromAccountId, toPhone, amount, description) => {
            paymentMutation.mutate({
              fromAccountId,
              toPhone,
              amount: parseFloat(amount),
              description
            })
          }}
          isLoading={paymentMutation.isPending || isPaymentProcessing}
        />
      )}

      <BottomNavigation />
    </div>
  )
}

function PaymentModal({
  amount,
  scannedData,
  accounts,
  onClose,
  onPay,
  isLoading,
}: {
  amount: string
  scannedData: string
  accounts: any[]
  onClose: () => void
  onPay: (fromAccountId: number, toPhone: string, amount: string, description: string) => void
  isLoading: boolean
}) {
  const [selectedAccountId, setSelectedAccountId] = useState<number>(
    accounts[0]?.id || accounts[0]?.accountId || 0
  )
  const [description, setDescription] = useState('Оплата по QR-коду')
  const [paymentAmount, setPaymentAmount] = useState(amount)

  // Обновляем paymentAmount при изменении amount
  useEffect(() => {
    setPaymentAmount(amount)
  }, [amount])

  // Парсим данные из QR-кода
  const parseQRData = (data: string) => {
    if (data.startsWith('payment:')) {
      const parts = data.replace('payment:', '').split(':')
      if (parts.length >= 2) {
        const parsedAmount = parseFloat(parts[0])
        if (!isNaN(parsedAmount)) {
          const identifier = parts.slice(1).join(':')
          if (identifier.startsWith('phone:')) {
            const phone = identifier.replace('phone:', '').replace(/[^\d]/g, '')
            return { type: 'phone' as const, value: phone, amount: parsedAmount }
          } else {
            // Пытаемся определить тип
            const cleanIdentifier = identifier.replace(/[^\d]/g, '')
            if (/^\d{10,15}$/.test(cleanIdentifier)) {
              return { type: 'phone' as const, value: cleanIdentifier, amount: parsedAmount }
            }
          }
        }
      }
    } else if (data.startsWith('phone:')) {
      const phone = data.replace('phone:', '').replace(/[^\d]/g, '')
      return { type: 'phone' as const, value: phone, amount: parseFloat(amount) || 0 }
    } else {
      const cleanData = data.replace(/[^\d]/g, '')
      if (/^\d{10,15}$/.test(cleanData)) {
        return { type: 'phone' as const, value: cleanData, amount: parseFloat(amount) || 0 }
      }
    }
    return { type: 'unknown' as const, value: data, amount: parseFloat(amount) || 0 }
  }

  const qrInfo = parseQRData(scannedData)
  const isPhone = qrInfo.type === 'phone'

  if (!isPhone) {
    return (
      <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4" onClick={onClose}>
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          className="w-full max-w-md rounded-2xl bg-white p-6 shadow-xl"
          onClick={(e) => e.stopPropagation()}
        >
          <div className="mb-4 flex items-center justify-between">
            <h3 className="text-xl font-bold text-gray-900">Ошибка</h3>
            <button onClick={onClose} className="rounded-full p-1 hover:bg-gray-100">
              <X className="h-5 w-5" />
            </button>
          </div>
          <p className="mb-4 text-gray-600">
            Отсканированный QR-код не содержит информацию о платеже. Поддерживаются только QR-коды с номером телефона.
          </p>
          <Button onClick={onClose} className="w-full">
            Закрыть
          </Button>
        </motion.div>
      </div>
    )
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4" onClick={onClose}>
      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        className="w-full max-w-md rounded-2xl bg-white p-6 shadow-xl"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="mb-4 flex items-center justify-between">
          <h3 className="text-xl font-bold text-gray-900">Подтверждение платежа</h3>
          <button onClick={onClose} className="rounded-full p-1 hover:bg-gray-100">
            <X className="h-5 w-5" />
          </button>
        </div>

        <div className="space-y-4">
          <div>
            <Label>Сумма (₽)</Label>
            {qrInfo.amount ? (
              <p className="text-2xl font-bold text-gray-900">{qrInfo.amount} ₽</p>
            ) : (
              <Input
                type="number"
                placeholder="1000"
                value={paymentAmount}
                onChange={(e) => setPaymentAmount(e.target.value)}
              />
            )}
          </div>

          <div>
            <p className="text-sm text-gray-500">Получатель</p>
            <p className="text-base font-medium text-gray-900">+{qrInfo.value}</p>
          </div>

          <div>
            <Label>Счет списания</Label>
            <select
              value={selectedAccountId}
              onChange={(e) => setSelectedAccountId(parseInt(e.target.value))}
              className="w-full rounded-lg border border-gray-300 px-3 py-2"
            >
              {accounts.map((acc) => (
                <option key={`${acc.clientId}-${acc.accountId || (acc as any).id}`} value={(acc as any).id || acc.accountId}>
                  {acc.accountName} ({acc.clientName})
                </option>
              ))}
            </select>
          </div>

          <div>
            <Label>Описание</Label>
            <Input
              type="text"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Назначение платежа"
            />
          </div>

          <div className="flex gap-3 pt-2">
            <Button variant="outline" onClick={onClose} className="flex-1" disabled={isLoading}>
              Отмена
            </Button>
            <Button
              onClick={() => {
                const finalAmount = qrInfo.amount || parseFloat(paymentAmount) || 0
                if (finalAmount <= 0) {
                  alert('❌ Укажите сумму платежа')
                  return
                }
                onPay(selectedAccountId, qrInfo.value, finalAmount.toString(), description)
              }}
              className="flex-1 bg-gradient-to-r from-purple-600 to-blue-600"
              disabled={isLoading || (!qrInfo.amount && (!paymentAmount || parseFloat(paymentAmount) <= 0))}
            >
              {isLoading ? 'Обработка...' : 'Оплатить'}
            </Button>
          </div>
        </div>
      </motion.div>
    </div>
  )
}
