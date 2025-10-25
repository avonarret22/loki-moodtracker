/**
 * API Client Wrapper para Loki Mood Tracker
 * Centraliza todas las llamadas al backend con manejo de errores y autenticación
 */

import { env } from './env';

const API_URL = env.NEXT_PUBLIC_API_URL;

/**
 * Error personalizado para errores de API
 */
export class ApiError extends Error {
  constructor(
    message: string,
    public status: number,
    public data?: any
  ) {
    super(message);
    this.name = 'ApiError';
  }
}

/**
 * Obtiene el token de autenticación del localStorage
 */
function getAuthToken(): string | null {
  if (typeof window === 'undefined') return null;
  return localStorage.getItem('loki_token');
}

/**
 * Maneja el caso de token expirado/inválido
 */
function handleAuthError(): void {
  if (typeof window === 'undefined') return;

  // Limpiar token
  localStorage.removeItem('loki_token');
  localStorage.removeItem('loki_user');

  // Redirigir a auth
  window.location.href = '/auth?error=session_expired';
}

/**
 * Cliente HTTP centralizado para hacer llamadas a la API
 *
 * @param endpoint - Endpoint relativo (e.g., '/api/v1/usuarios')
 * @param options - Opciones de fetch
 * @returns Promise con los datos parseados
 * @throws ApiError si la respuesta no es exitosa
 *
 * @example
 * ```typescript
 * const user = await apiCall<UserData>('/api/v1/auth/me');
 * const moods = await apiCall<MoodData[]>('/api/v1/usuarios/1/estados_animo/');
 * ```
 */
export async function apiCall<T>(
  endpoint: string,
  options?: RequestInit
): Promise<T> {
  const token = getAuthToken();

  // Construir headers
  const headers: HeadersInit = {
    'Content-Type': 'application/json',
    ...options?.headers,
  };

  // Agregar token si existe
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  try {
    const response = await fetch(`${API_URL}${endpoint}`, {
      ...options,
      headers,
    });

    // Manejar errores de autenticación
    if (response.status === 401) {
      handleAuthError();
      throw new ApiError('Sesión expirada', 401);
    }

    // Manejar otros errores
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new ApiError(
        errorData.detail || errorData.message || 'Error en la petición',
        response.status,
        errorData
      );
    }

    // Parsear respuesta
    return response.json();
  } catch (error) {
    // Re-throw ApiError
    if (error instanceof ApiError) {
      throw error;
    }

    // Wrap otros errores
    console.error('API Call Error:', error);
    throw new ApiError(
      'Error de conexión con el servidor',
      0,
      { originalError: error }
    );
  }
}

/**
 * Helper para GET requests
 */
export async function get<T>(endpoint: string): Promise<T> {
  return apiCall<T>(endpoint, { method: 'GET' });
}

/**
 * Helper para POST requests
 */
export async function post<T>(
  endpoint: string,
  data: any
): Promise<T> {
  return apiCall<T>(endpoint, {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

/**
 * Helper para PUT requests
 */
export async function put<T>(
  endpoint: string,
  data: any
): Promise<T> {
  return apiCall<T>(endpoint, {
    method: 'PUT',
    body: JSON.stringify(data),
  });
}

/**
 * Helper para DELETE requests
 */
export async function del<T>(endpoint: string): Promise<T> {
  return apiCall<T>(endpoint, { method: 'DELETE' });
}

// ===== TIPOS =====

export interface UserData {
  id: number;
  nombre: string;
  telefono: string;
  fecha_registro: string;
  nivel_confianza?: number;
  total_interacciones?: number;
  moods?: MoodData[];
  trust_level?: TrustLevel;
}

export interface MoodData {
  id: number;
  timestamp: string;
  nivel: number;
  notas_texto?: string;
  contexto_extraido?: string;
  disparadores_detectados?: string;
}

export interface TrustLevel {
  nivel_confianza: number;
  total_interacciones: number;
  nivel_nombre: string;
  mensajes_hasta_siguiente_nivel: number;
  es_nivel_maximo?: boolean;
}

export interface HabitData {
  id: number;
  nombre_habito: string;
  categoria: string;
  objetivo_semanal: number;
  activo: boolean;
  fecha_creacion: string;
}

export interface PatternAnalysis {
  has_enough_data: boolean;
  data_points: number;
  average_mood: number;
  mood_stability: number;
  correlations: Array<{
    factor: string;
    correlation: number;
    significance: number;
  }>;
  insights: string[];
}
