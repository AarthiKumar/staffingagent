import * as React from "react"
import { cn } from "@/lib/utils"

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "default" | "secondary" | "outline"
  size?: "default" | "sm" | "lg"
  asChild?: boolean
}

const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant = "default", size = "default", asChild = false, ...props }, ref) => {
    const variantClasses = {
      default: "bg-blue-600 text-white hover:bg-blue-700",
      secondary: "bg-gray-200 text-gray-900 hover:bg-gray-300",
      outline: "border border-gray-300 bg-white hover:bg-gray-50",
    }

    const sizeClasses = {
      default: "px-4 py-2",
      sm: "px-3 py-1.5 text-xs",
      lg: "px-6 py-3 text-base",
    }

    const Comp = asChild ? React.Fragment : "button"

    const classes = cn(
      "inline-flex items-center justify-center rounded-md text-sm font-medium transition-colors focus:outline-none focus:ring-2 focus:ring-offset-2 disabled:opacity-50 disabled:pointer-events-none",
      variantClasses[variant],
      sizeClasses[size],
      className
    )

    if (asChild && props.children) {
      return React.cloneElement(props.children as React.ReactElement, {
        className: classes,
      })
    }

    return (
      <button
        className={classes}
        ref={ref}
        {...props}
      />
    )
  }
)
Button.displayName = "Button"

export { Button }
