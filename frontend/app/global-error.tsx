'use client';

/**
 * Global Error Boundary
 * Captura errores que ocurren en el root layout
 * Debe renderizar su propio <html> y <body>
 */

import { useEffect } from 'react';

export default function GlobalError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    console.error('Global Application Error:', error);
  }, [error]);

  return (
    <html lang="es">
      <body>
        <div className="min-h-screen flex items-center justify-center bg-gray-50 px-4">
          <div className="max-w-md w-full text-center">
            <div className="text-6xl mb-4">⚠️</div>

            <h2 className="text-2xl font-bold mb-2 text-gray-900">
              Error Crítico
            </h2>

            <p className="text-gray-600 mb-6">
              La aplicación encontró un error crítico. Por favor, recarga la
              página o contacta con soporte si el problema persiste.
            </p>

            <div className="space-y-3">
              <button
                onClick={reset}
                className="w-full px-4 py-3 bg-purple-600 text-white rounded-lg
                         hover:bg-purple-700 transition-colors font-medium"
              >
                Intentar de nuevo
              </button>

              <button
                onClick={() => window.location.href = '/'}
                className="w-full px-4 py-3 bg-gray-200 text-gray-800 rounded-lg
                         hover:bg-gray-300 transition-colors font-medium"
              >
                Volver al inicio
              </button>
            </div>

            {process.env.NODE_ENV === 'development' && (
              <details className="mt-8 text-left bg-gray-100 rounded-lg p-4">
                <summary className="cursor-pointer text-sm font-medium">
                  Detalles técnicos
                </summary>
                <pre className="mt-3 text-xs overflow-auto max-h-64">
                  {error.message}
                  {'\n\n'}
                  {error.stack}
                </pre>
              </details>
            )}
          </div>
        </div>
      </body>
    </html>
  );
}
