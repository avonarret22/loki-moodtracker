'use client';

import { Suspense, useEffect, useState } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';

// Componente interno que usa useSearchParams
function AuthContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [status, setStatus] = useState<'loading' | 'success' | 'error'>('loading');
  const [message, setMessage] = useState('Verificando tu acceso...');

  useEffect(() => {
    const token = searchParams.get('token');
    
    if (!token) {
      setStatus('error');
      setMessage('No se proporcionó un token de acceso');
      return;
    }

    // Verificar el token con el backend
    const verifyToken = async (token: string) => {
      try {
        const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
        
        const response = await fetch(`${apiUrl}/api/v1/auth/verify-token`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ token }),
        });

        const data = await response.json();

        if (data.valid) {
          // Token válido, guardar en localStorage y redirigir
          localStorage.setItem('loki_token', token);
          localStorage.setItem('loki_user', JSON.stringify({
            usuario_id: data.usuario_id,
            telefono: data.telefono,
          }));
          
          setStatus('success');
          setMessage('¡Acceso verificado! Redirigiendo...');
          
          // Redirigir al dashboard después de 1 segundo
          setTimeout(() => {
            router.push('/dashboard');
          }, 1000);
        } else {
          setStatus('error');
          setMessage('El token es inválido o ha expirado');
        }
      } catch (error) {
        console.error('Error verificando token:', error);
        setStatus('error');
        setMessage('Error al verificar el acceso. Intenta de nuevo.');
      }
    };

    verifyToken(token);
  }, [searchParams, router]);

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-600 via-pink-500 to-orange-400 flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl shadow-2xl p-8 max-w-md w-full">
        <div className="text-center">
          {/* Logo/Icon */}
          <div className="mb-6">
            <div className="w-20 h-20 bg-gradient-to-br from-purple-500 to-pink-500 rounded-full mx-auto flex items-center justify-center">
              <span className="text-4xl">🤖</span>
            </div>
          </div>

          {/* Título */}
          <h1 className="text-3xl font-bold text-gray-800 mb-2">
            Loki Dashboard
          </h1>
          <p className="text-gray-600 mb-8">
            Tu compañero de bienestar emocional
          </p>

          {/* Estado */}
          <div className="mb-6">
            {status === 'loading' && (
              <div className="flex flex-col items-center">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-600 mb-4"></div>
                <p className="text-gray-700">{message}</p>
              </div>
            )}

            {status === 'success' && (
              <div className="flex flex-col items-center">
                <div className="w-12 h-12 bg-green-100 rounded-full flex items-center justify-center mb-4">
                  <span className="text-2xl">✅</span>
                </div>
                <p className="text-green-600 font-semibold">{message}</p>
              </div>
            )}

            {status === 'error' && (
              <div className="flex flex-col items-center">
                <div className="w-12 h-12 bg-red-100 rounded-full flex items-center justify-center mb-4">
                  <span className="text-2xl">❌</span>
                </div>
                <p className="text-red-600 font-semibold">{message}</p>
                <p className="text-gray-600 text-sm mt-4">
                  Solicita un nuevo enlace desde WhatsApp escribiendo &quot;dashboard&quot;
                </p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

// Componente principal exportado con Suspense boundary
export default function AuthPage() {
  return (
    <Suspense fallback={
      <div className="min-h-screen bg-gradient-to-br from-purple-600 via-pink-500 to-orange-400 flex items-center justify-center p-4">
        <div className="bg-white rounded-2xl shadow-2xl p-8 max-w-md w-full">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-600 mx-auto mb-4"></div>
            <p className="text-gray-700">Cargando...</p>
          </div>
        </div>
      </div>
    }>
      <AuthContent />
    </Suspense>
  );
}
