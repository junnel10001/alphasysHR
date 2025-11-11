import { useEffect, useRef, useState } from 'react'

export function useDropdownKeyboard() {
  const [isOpen, setIsOpen] = useState(false)
  const triggerRef = useRef<HTMLButtonElement>(null)

  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      if (!isOpen) return

      switch (event.key) {
        case 'Escape':
          // Close dropdown on Escape
          setIsOpen(false)
          break
        case 'ArrowDown':
          // Move focus to next item
          event.preventDefault()
          moveFocus(1)
          break
        case 'ArrowUp':
          // Move focus to previous item
          event.preventDefault()
          moveFocus(-1)
          break
        case 'Home':
          // Move focus to first item
          event.preventDefault()
          moveFocusToFirst()
          break
        case 'End':
          // Move focus to last item
          event.preventDefault()
          moveFocusToLast()
          break
      }
    }

    const moveFocus = (direction: number) => {
      const dropdown = document.querySelector('[data-dropdown-content]')
      if (!dropdown) return

      const items = Array.from(dropdown.querySelectorAll('[role="menuitem"]'))
      if (items.length === 0) return

      const focusedItem = document.activeElement
      if (!focusedItem) return
      
      const currentIndex = items.indexOf(focusedItem as HTMLElement)
      if (currentIndex === -1) return
      
      let nextIndex = currentIndex + direction
      if (nextIndex < 0) nextIndex = items.length - 1
      if (nextIndex >= items.length) nextIndex = 0

      ;(items[nextIndex] as HTMLElement)?.focus()
    }

    const moveFocusToFirst = () => {
      const dropdown = document.querySelector('[data-dropdown-content]')
      if (!dropdown) return

      const items = Array.from(dropdown.querySelectorAll('[role="menuitem"]'))
      if (items.length > 0) {
        ;(items[0] as HTMLElement)?.focus()
      }
    }

    const moveFocusToLast = () => {
      const dropdown = document.querySelector('[data-dropdown-content]')
      if (!dropdown) return

      const items = Array.from(dropdown.querySelectorAll('[role="menuitem"]'))
      if (items.length > 0) {
        ;(items[items.length - 1] as HTMLElement)?.focus()
      }
    }

    document.addEventListener('keydown', handleKeyDown)
    return () => document.removeEventListener('keydown', handleKeyDown)
  }, [isOpen])

  const toggleDropdown = () => {
    setIsOpen(!isOpen)
  }

  return { triggerRef, isOpen, toggleDropdown }
}