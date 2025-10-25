/**
 * Validación de variables de entorno con Zod
 * Falla en build time si las variables no están configuradas correctamente
 */

import { z } from 'zod';

// Schema de validación
const envSchema = z.object({
  NEXT_PUBLIC_API_URL: z
    .string()
    .url('NEXT_PUBLIC_API_URL debe ser una URL válida')
    .min(1, 'NEXT_PUBLIC_API_URL es requerida'),

  NEXT_PUBLIC_ENV: z
    .enum(['development', 'staging', 'production'])
    .default('development'),

  NEXT_PUBLIC_SENTRY_DSN: z
    .string()
    .url()
    .optional(),
});

// Validar variables de entorno
const parsedEnv = envSchema.safeParse({
  NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL,
  NEXT_PUBLIC_ENV: process.env.NEXT_PUBLIC_ENV || 'development',
  NEXT_PUBLIC_SENTRY_DSN: process.env.NEXT_PUBLIC_SENTRY_DSN,
});

if (!parsedEnv.success) {
  console.error('❌ Variables de entorno inválidas:');
  console.error(parsedEnv.error.flatten().fieldErrors);
  throw new Error(
    'Invalid environment variables. Check console for details.'
  );
}

/**
 * Variables de entorno validadas y type-safe
 * @example
 * ```typescript
 * import { env } from '@/lib/env';
 *
 * const apiUrl = env.NEXT_PUBLIC_API_URL;
 * const isDev = env.NEXT_PUBLIC_ENV === 'development';
 * ```
 */
export const env = parsedEnv.data;

/**
 * Helper para verificar si estamos en desarrollo
 */
export const isDevelopment = env.NEXT_PUBLIC_ENV === 'development';

/**
 * Helper para verificar si estamos en producción
 */
export const isProduction = env.NEXT_PUBLIC_ENV === 'production';
