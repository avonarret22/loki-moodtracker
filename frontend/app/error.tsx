'use client';

/**
 * Error Boundary para la aplicación
 * Captura errores en tiempo de ejecución y muestra UI de fallback
 */

import { useEffect } from 'react';

export default function Error({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    // Log error a servicio de monitoreo (Sentry, etc.)
    console.error('Application Error:', error);
  }, [error]);

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 px-4">
      <div className="max-w-md w-full text-center">
        {/* Icono de error */}
        <div className="text-6xl mb-4">😞</div>

        {/* Título */}
        <h2 className="text-2xl font-bold mb-2 text-gray-900">
          Algo salió mal
        </h2>

        {/* Descripción */}
        <p className="text-gray-600 mb-6">
          Ocurrió un error inesperado. Nuestro equipo ha sido notificado y
          estamos trabajando para solucionarlo.
        </p>

        {/* Acciones */}
        <div className="space-y-3">
          <button
            onClick={reset}
            className="w-full px-4 py-3 bg-purple-600 text-white rounded-lg
                     hover:bg-purple-700 transition-colors font-medium
                     focus:outline-none focus:ring-2 focus:ring-purple-500 focus:ring-offset-2"
          >
            Intentar de nuevo
          </button>

          <a
            href="/"
            className="block w-full px-4 py-3 bg-gray-200 text-gray-800 rounded-lg
                     hover:bg-gray-300 transition-colors font-medium
                     focus:outline-none focus:ring-2 focus:ring-gray-400 focus:ring-offset-2"
          >
            Volver al inicio
          </a>
        </div>

        {/* Detalles técnicos (solo en desarrollo) */}
        {process.env.NODE_ENV === 'development' && (
          <details className="mt-8 text-left bg-gray-100 rounded-lg p-4">
            <summary className="cursor-pointer text-sm font-medium text-gray-700 hover:text-gray-900">
              Detalles técnicos (dev only)
            </summary>
            <pre className="mt-3 text-xs text-gray-600 overflow-auto max-h-64">
              {error.message}
              {'\n\n'}
              {error.stack}
            </pre>
            {error.digest && (
              <p className="mt-2 text-xs text-gray-500">
                Error ID: {error.digest}
              </p>
            )}
          </details>
        )}
      </div>
    </div>
  );
}
