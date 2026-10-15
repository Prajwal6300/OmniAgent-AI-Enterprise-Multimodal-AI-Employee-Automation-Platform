import { createContext, useContext, useState } from 'react';

interface Toast {
  id: string;
  type: 'success' | 'error';
  message: string;
}

interface ToastContextValue {
  showToast: (toast: Omit<Toast, 'id'>) => void;
  toast: Toast | null;
  setToast: React.Dispatch<React.SetStateAction<Toast | null>>;
}

const ToastContext = createContext<ToastContextValue | undefined>(undefined);

export const useToast = (): ToastContextValue => useContext(ToastContext) as ToastContextValue;

export const ToastProvider: React.FC<{ children: React.ReactNode }> = ({
  children,
}) => {
  const [toast, setToast] = useState<Toast | null>(null);

  const showToast = (toast: Omit<Toast, 'id'>) => {
    const id = crypto.randomUUID();
    setToast({ ...toast, id });
    const timer = setTimeout(() => setToast(null), 4000);
    return () => clearTimeout(timer);
  };

  return (
    <ToastContext.Provider value={{ showToast, toast, setToast }}>{children}</ToastContext.Provider>
  );
};

export const Toaster: React.FC = () => {
  const { toast, setToast } = useToast();

  return (
    <div
      aria-live="polite"
      className="fixed top-4 right-4 z-50 flex flex-col gap-2 pointer-events-none"
    >
      {toast && (
        <div className="p-4 rounded-lg border max-w-xs w-full fade-in from-top-toast bg-slate-950 text-slate-100">
          <div className="flex items-center justify-between gap-2">
            <span className="text-sm">{toast.message}</span>
            <button
              onClick={() => setToast(null)}
              aria-label="Dismiss message"
              className="text-xs opacity-50 hover:opacity-100"
            >
              ✕
            </button>
          </div>
        </div>
      )}
    </div>
  );
};