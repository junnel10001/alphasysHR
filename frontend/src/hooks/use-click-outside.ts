import { useEffect, useRef, useState } from 'react'

export function useClickOutside<T extends HTMLElement>(
  initialIsOpen: boolean = false
) {
  const [isOpen, setIsOpen] = useState(initialIsOpen)
  const ref = useRef<T>(null)

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (ref.current && !ref.current.contains(event.target as Node)) {
        setIsOpen(false)
      }
    }

    const handleEscapeKey = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        setIsOpen(false)
      }
    }

    const handleMouseDown = (event: MouseEvent) => {
      handleClickOutside(event)
    }

    const handleKeyDown = (event: KeyboardEvent) => {
      handleEscapeKey(event)
    }

    document.addEventListener('mousedown', handleMouseDown)
    document.addEventListener('keydown', handleKeyDown)

    return () => {
      document.removeEventListener('mousedown', handleMouseDown)
      document.removeEventListener('keydown', handleKeyDown)
    }
  }, [])

  const toggle = () => setIsOpen(!isOpen)
  const open = () => setIsOpen(true)
  const close = () => setIsOpen(false)

  return {
    ref,
    isOpen,
    toggle,
    open,
    close,
  }
}