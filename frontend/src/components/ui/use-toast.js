import { useState, useCallback, createContext, useContext } from 'react';

const ToastContext = createContext();

export const useToast = () => {
  const context = useContext(ToastContext);
  if (!context) {
    // Fallback implementation if ToastProvider is not available
    return {
      toast: ({ title, description, variant = 'default' }) => {
        console.log(`Toast: ${title} - ${description} (${variant})`);
        
        // Simple browser notification as fallback
        if (title && description) {
          alert(`${title}: ${description}`);
        } else if (title) {
          alert(title);
        } else if (description) {
          alert(description);
        }
      }
    };
  }
  return context;
};

export const ToastProvider = ({ children }) => {
  const [toasts, setToasts] = useState([]);

  const toast = useCallback(({ title, description, variant = 'default', duration = 5000 }) => {
    const id = Math.random().toString(36).substr(2, 9);
    const newToast = { id, title, description, variant, duration };
    
    setToasts(prev => [...prev, newToast]);
    
    // Auto remove toast after duration
    setTimeout(() => {
      setToasts(prev => prev.filter(t => t.id !== id));
    }, duration);
    
    return { id };
  }, []);

  const dismissToast = useCallback((id) => {
    setToasts(prev => prev.filter(t => t.id !== id));
  }, []);

  return (
    <ToastContext.Provider value={{ toast, toasts, dismissToast }}>
      {children}
      {/* Render toasts */}
      <div className="fixed bottom-0 right-0 z-50 p-4 space-y-2">
        {toasts.map((t) => (
          <div
            key={t.id}
            className={`max-w-sm w-full bg-white shadow-lg rounded-lg pointer-events-auto border-l-4 ${
              t.variant === 'destructive' 
                ? 'border-red-500 bg-red-50' 
                : t.variant === 'success'
                ? 'border-green-500 bg-green-50'
                : 'border-blue-500'
            }`}
          >
            <div className="p-4">
              <div className="flex items-start">
                <div className="ml-3 w-0 flex-1 pt-0.5">
                  {t.title && (
                    <p className={`text-sm font-medium ${
                      t.variant === 'destructive' 
                        ? 'text-red-900' 
                        : t.variant === 'success'
                        ? 'text-green-900'
                        : 'text-gray-900'
                    }`}>
                      {t.title}
                    </p>
                  )}
                  {t.description && (
                    <p className={`mt-1 text-sm ${
                      t.variant === 'destructive' 
                        ? 'text-red-700' 
                        : t.variant === 'success'
                        ? 'text-green-700'
                        : 'text-gray-500'
                    }`}>
                      {t.description}
                    </p>
                  )}
                </div>
                <div className="ml-4 flex-shrink-0 flex">
                  <button
                    className={`rounded-md inline-flex ${
                      t.variant === 'destructive' 
                        ? 'text-red-400 hover:text-red-500' 
                        : t.variant === 'success'
                        ? 'text-green-400 hover:text-green-500'
                        : 'text-gray-400 hover:text-gray-500'
                    } focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500`}
                    onClick={() => dismissToast(t.id)}
                  >
                    <span className="sr-only">Close</span>
                    <svg className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                      <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" />
                    </svg>
                  </button>
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>
    </ToastContext.Provider>
  );
};

export default useToast;