import React from 'react';

interface ErrorBoundaryProps {
  children: React.ReactNode;
}

export default function ErrorBoundary({ children }: ErrorBoundaryProps) {
  const [hasError, setHasError] = React.useState(false);

  const handleError = (error: Error) => {
    setHasError(true);
    console.error('Error caught by Boundary:', error);
  };

  return (
    <div className="min-h-screen bg-parchment text-slate-100 p-8">
      {hasError && (
        <>
          <h1 className="text-2xl font-bold tracking-tight text-warm-mist mb-4">
            Something Went Wrong
          </h1>
          <p className="text-slate-600 mb-6">
            An unexpected error occurred. Please try again or go back to the Home page.
          </p>
          <a href="/" className="bg-indigo-600 hover:bg-indigo-700 text-white px-4 py-2 rounded">
            <span className="mr-2" /> Home
          </a>
          <a href="/dashboard" className="bg-indigo-600 hover:bg-indigo-700 text-white px-4 py-2 rounded">
            <span className="mr-2" /> Dashboard
          </a>
        </>
      )}
      {children}
    </div>
  );
}