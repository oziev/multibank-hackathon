import * as React from 'react'
import { cn } from '@shared/lib/utils'

interface ProgressProps extends React.HTMLAttributes<HTMLDivElement> {
  value?: number
  indicatorColor?: string
  showLabel?: boolean
}

const Progress = React.forwardRef<HTMLDivElement, ProgressProps>(
  ({ className, value = 0, indicatorColor, showLabel = false, ...props }, ref) => {
    const percentage = Math.min(Math.max(value, 0), 100)
    
    return (
      <div className="space-y-1">
        <div
          ref={ref}
          className={cn(
            'relative h-3 w-full overflow-hidden rounded-full bg-muted',
            className
          )}
          {...props}
        >
          <div
            className={cn(
              'h-full transition-all duration-500 ease-out',
              indicatorColor || 'bg-primary'
            )}
            style={{ 
              width: `${percentage}%`,
              transform: 'translateX(0%)'
            }}
          />
        </div>
        {showLabel && (
          <div className="flex justify-between text-xs text-muted-foreground">
            <span>{percentage.toFixed(0)}%</span>
          </div>
        )}
      </div>
    )
  }
)
Progress.displayName = 'Progress'

export { Progress }

