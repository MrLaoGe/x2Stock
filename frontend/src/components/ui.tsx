import type { ButtonHTMLAttributes, InputHTMLAttributes, ReactNode, SelectHTMLAttributes } from 'react'

type ButtonProps = ButtonHTMLAttributes<HTMLButtonElement> & { variant?: 'primary' | 'secondary' }

export function Button({ variant = 'primary', className = '', ...props }: ButtonProps) {
  return <button className={`button ${variant === 'secondary' ? 'secondary' : ''} ${className}`} {...props} />
}

export function TextInput({ className = '', ...props }: InputHTMLAttributes<HTMLInputElement>) {
  return <input className={`text-input ${className}`} {...props} />
}

export function SelectInput({ className = '', children, ...props }: SelectHTMLAttributes<HTMLSelectElement>) {
  return <select className={`select-input ${className}`} {...props}>{children}</select>
}

export function Notice({ children }: { children: ReactNode }) {
  return <div className="notice"><span className="notice-dot" aria-hidden="true" />{children}</div>
}
