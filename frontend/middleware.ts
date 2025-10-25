/**
 * Middleware de Next.js para proteger rutas
 * Se ejecuta en el edge antes de renderizar las páginas
 */

import { NextRequest, NextResponse } from 'next/server';

// URL del API (debe coincidir con el backend)
const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// Rutas públicas (no requieren autenticación)
const PUBLIC_ROUTES = ['/', '/auth'];

/**
 * Verifica si la ruta es pública
 */
function isPublicRoute(pathname: string): boolean {
  return PUBLIC_ROUTES.some(route => pathname === route || pathname.startsWith(route));
}

/**
 * Middleware principal
 * Ejecuta validación de auth en cada request
 */
export async function middleware(request: NextRequest) {
  const pathname = request.nextUrl.pathname;

  // Permitir rutas públicas
  if (isPublicRoute(pathname)) {
    return NextResponse.next();
  }

  // Rutas protegidas - verificar token
  if (pathname.startsWith('/dashboard')) {
    const token = request.cookies.get('loki_token')?.value;

    // Sin token -> redirigir a auth
    if (!token) {
      const url = new URL('/auth', request.url);
      url.searchParams.set('error', 'auth_required');
      url.searchParams.set('returnTo', pathname);
      return NextResponse.redirect(url);
    }

    // Validar token en backend (opcional pero recomendado)
    try {
      const response = await fetch(`${API_URL}/api/v1/auth/verify-token`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ token }),
      });

      if (!response.ok) {
        // Token inválido -> limpiar y redirigir
        const url = new URL('/auth', request.url);
        url.searchParams.set('error', 'session_expired');

        const res = NextResponse.redirect(url);
        res.cookies.delete('loki_token');
        return res;
      }
    } catch (error) {
      console.error('Error validating token:', error);
      // En caso de error de red, permitir acceso (evitar bloquear usuario)
      // En producción podrías querer ser más estricto
    }
  }

  return NextResponse.next();
}

/**
 * Configuración del middleware
 * Define en qué rutas se ejecuta
 */
export const config = {
  matcher: [
    /*
     * Match all request paths except for the ones starting with:
     * - api (API routes)
     * - _next/static (static files)
     * - _next/image (image optimization files)
     * - favicon.ico (favicon file)
     */
    '/((?!api|_next/static|_next/image|favicon.ico).*)',
  ],
};
