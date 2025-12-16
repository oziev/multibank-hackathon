export type AnalyticsOverview = {
  totalBalance: number
  accountsCount: number
  currentMonth: {
    expenses: number
    income: number
    expenseChange: number
    incomeChange: number
  }
  topCategories: Array<{
    category: string
    categoryName: string
    amount: number
    percentage: number
  }>
}

export type CategoryBreakdown = {
  category: string
  categoryName: string
  amount: number
  count: number
  percentage: number
}

