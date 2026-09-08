import { createContext, useCallback, useContext, useRef, useState } from 'react'

const ConfirmContext = createContext(null)

export function ConfirmProvider({ children }) {
  const [state, setState] = useState(null) // { message, confirmText } | null
  const resolver = useRef(null)

  // Returns a Promise<boolean> — components `await confirm(...)` instead of
  // relying on the browser's native confirm(), which we can't restyle.
  const confirm = useCallback((message, confirmText = 'Delete') => {
    setState({ message, confirmText })
    return new Promise((resolve) => {
      resolver.current = resolve
    })
  }, [])

  function handleConfirm() {
    resolver.current?.(true)
    setState(null)
  }

  function handleCancel() {
    resolver.current?.(false)
    setState(null)
  }

  return (
    <ConfirmContext.Provider value={confirm}>
      {children}
      <div
        className={`confirm-modal-overlay ${state ? 'is-open' : ''}`}
        onClick={(e) => { if (e.target === e.currentTarget) handleCancel() }}
      >
        {state && (
          <div className="confirm-modal">
            <p className="confirm-modal__message">{state.message}</p>
            <div className="confirm-modal__actions">
              <button type="button" className="btn btn--ghost btn--sm" onClick={handleCancel}>
                Cancel
              </button>
              <button type="button" className="btn btn--primary btn--sm" onClick={handleConfirm}>
                {state.confirmText}
              </button>
            </div>
          </div>
        )}
      </div>
    </ConfirmContext.Provider>
  )
}

export function useConfirm() {
  const ctx = useContext(ConfirmContext)
  if (!ctx) throw new Error('useConfirm must be used within ConfirmProvider')
  return ctx
}