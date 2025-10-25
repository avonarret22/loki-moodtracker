'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';

interface UserData {
  id: number;
  nombre: string;
  telefono: string;
  fecha_registro: string;
  nivel_CMV: string;
  frecuencia_checkins: string;
}

interface MoodData {
  timestamp: string;
  nivel: number;
  notas_texto: string;
}

export default function DashboardPage() {
  const router = useRouter();
  const [user, setUser] = useState<UserData | null>(null);
  const [moods, setMoods] = useState<MoodData[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Verificar si hay token
    const token = localStorage.getItem('loki_token');
    if (!token) {
      router.push('/auth');
      return;
    }

    loadUserData(token);
  }, [router]);

  const loadUserData = async (token: string) => {
    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
      
      // Obtener datos del usuario
      const userResponse = await fetch(`${apiUrl}/api/v1/auth/me?token=${token}`);
      const userData = await userResponse.json();
      setUser(userData);

      // Obtener datos de mood
      // TODO: Implementar endpoint en backend para obtener moods del usuario
      setMoods([]);
      
      setLoading(false);
    } catch (error) {
      console.error('Error cargando datos:', error);
      setLoading(false);
    }
  };

  const handleLogout = () => {
    localStorage.removeItem('loki_token');
    localStorage.removeItem('loki_user');
    router.push('/');
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-600"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex justify-between items-center">
            <div className="flex items-center space-x-3">
              <span className="text-3xl">🤖</span>
              <h1 className="text-2xl font-bold text-gray-900">Loki Dashboard</h1>
            </div>
            <button
              onClick={handleLogout}
              className="px-4 py-2 text-sm text-gray-700 hover:text-gray-900"
            >
              Cerrar sesión
            </button>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Welcome Section */}
        <div className="bg-gradient-to-r from-purple-600 to-pink-500 rounded-2xl p-8 text-white mb-8">
          <h2 className="text-3xl font-bold mb-2">
            ¡Hola, {user?.nombre || 'Usuario'}! 👋
          </h2>
          <p className="text-purple-100">
            Bienvenido a tu dashboard personal de bienestar emocional
          </p>
        </div>

        {/* Stats Grid */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          {/* Card 1 */}
          <div className="bg-white rounded-xl shadow-sm p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-gray-600 font-medium">Estado promedio</h3>
              <span className="text-2xl">📊</span>
            </div>
            <div className="text-3xl font-bold text-gray-900">
              {moods.length > 0 ? 
                (moods.reduce((acc, m) => acc + m.nivel, 0) / moods.length).toFixed(1) : 
                'N/A'
              }
            </div>
            <p className="text-sm text-gray-500 mt-1">Últimos 30 días</p>
          </div>

          {/* Card 2 */}
          <div className="bg-white rounded-xl shadow-sm p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-gray-600 font-medium">Registros totales</h3>
              <span className="text-2xl">📝</span>
            </div>
            <div className="text-3xl font-bold text-gray-900">{moods.length}</div>
            <p className="text-sm text-gray-500 mt-1">Entradas guardadas</p>
          </div>

          {/* Card 3 */}
          <div className="bg-white rounded-xl shadow-sm p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-gray-600 font-medium">Días activo</h3>
              <span className="text-2xl">🔥</span>
            </div>
            <div className="text-3xl font-bold text-gray-900">
              {user?.fecha_registro ? 
                Math.floor((Date.now() - new Date(user.fecha_registro).getTime()) / (1000 * 60 * 60 * 24)) :
                0
              }
            </div>
            <p className="text-sm text-gray-500 mt-1">Desde que te registraste</p>
          </div>
        </div>

        {/* Coming Soon */}
        <div className="bg-white rounded-xl shadow-sm p-8 text-center">
          <span className="text-6xl mb-4 block">🚧</span>
          <h3 className="text-2xl font-bold text-gray-900 mb-2">
            Dashboard en construcción
          </h3>
          <p className="text-gray-600 mb-6">
            Pronto podrás ver gráficas detalladas de tu estado de ánimo, <br />
            seguimiento de hábitos, patrones emocionales y más.
          </p>
          <div className="inline-flex items-center space-x-2 text-purple-600">
            <span>Sigue usando Loki por WhatsApp</span>
            <span>💬</span>
          </div>
        </div>
      </main>
    </div>
  );
}
