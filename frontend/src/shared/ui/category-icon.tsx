import { cn } from '@shared/lib/utils'
import { 
  ShoppingCart, 
  UtensilsCrossed, 
  Car, 
  Shirt, 
  Heart, 
  Gamepad2, 
  Plane, 
  Dumbbell, 
  Sparkles, 
  Phone, 
  GraduationCap, 
  Baby, 
  Home, 
  ArrowRightLeft, 
  FileText 
} from 'lucide-react'

const categoryIcons: Record<string, any> = {
  groceries: ShoppingCart,
  restaurants: UtensilsCrossed,
  transport: Car,
  clothing: Shirt,
  health: Heart,
  entertainment: Gamepad2,
  travel: Plane,
  sports: Dumbbell,
  beauty: Sparkles,
  utilities: Phone,
  education: GraduationCap,
  children: Baby,
  home: Home,
  transfers: ArrowRightLeft,
  other: FileText,
}

const categoryColors: Record<string, string> = {
  groceries: 'bg-green-100 text-green-600',
  restaurants: 'bg-orange-100 text-orange-600',
  transport: 'bg-blue-100 text-blue-600',
  clothing: 'bg-purple-100 text-purple-600',
  health: 'bg-red-100 text-red-600',
  entertainment: 'bg-pink-100 text-pink-600',
  travel: 'bg-cyan-100 text-cyan-600',
  sports: 'bg-emerald-100 text-emerald-600',
  beauty: 'bg-fuchsia-100 text-fuchsia-600',
  utilities: 'bg-yellow-100 text-yellow-600',
  education: 'bg-indigo-100 text-indigo-600',
  children: 'bg-rose-100 text-rose-600',
  home: 'bg-amber-100 text-amber-600',
  transfers: 'bg-violet-100 text-violet-600',
  other: 'bg-gray-100 text-gray-600',
}

type CategoryIconProps = {
  category: string
  className?: string
}

export function CategoryIcon({ category, className }: CategoryIconProps) {
  const Icon = categoryIcons[category] || FileText
  
  return <Icon className={cn('h-4 w-4', className)} />
}

type CategoryBadgeProps = {
  category: string
  categoryName?: string
  className?: string
}

export function CategoryBadge({ category, categoryName, className }: CategoryBadgeProps) {
  const Icon = categoryIcons[category] || FileText
  const colorClass = categoryColors[category] || 'bg-gray-100 text-gray-600'
  
  return (
    <div className={cn('inline-flex items-center gap-1.5 rounded-full px-2.5 py-1', colorClass, className)}>
      <Icon className="h-3.5 w-3.5" />
      {categoryName && <span className="text-xs font-medium">{categoryName}</span>}
    </div>
  )
}

