'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import dynamic from 'next/dynamic';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';

const MoodTrendChart = dynamic(() => import('@/components/charts').then(mod => mod.MoodTrendChart), {
  ssr: false,
  loading: () => <div className="h-[250px] flex items-center justify-center"><div className="animate-spin rounded-full h-8 w-8 border-b-2 border-purple-600"></div></div>
});

const ActivitiesChart = dynamic(() => import('@/components/charts').then(mod => mod.ActivitiesChart), {
  ssr: false,
  loading: () => <div className="h-[250px] flex items-center justify-center"><div className="animate-spin rounded-full h-8 w-8 border-b-2 border-pink-600"></div></div>
});

interface MoodData {
  timestamp: string;
  nivel: number;
  notas_texto?: string;
}

interface TrustLevel {
  nivel_confianza: number;
  total_interacciones: number;
  nivel_nombre: string;
  nivel_descripcion?: string;
  mensajes_hasta_siguiente_nivel: number;
  es_nivel_maximo?: boolean;
}

interface UserData {
  id: number;
  nombre: string;
  telefono: string;
  fecha_registro: string;
  nivel_CMV?: number;
  frecuencia_checkins?: string;
  moods?: MoodData[];
  trust_level?: TrustLevel;
}

export default function DashboardPage() {
  const router = useRouter();
  const [userData, setUserData] = useState<UserData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const loadUserData = async (token: string) => {
      try {
        const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
        const response = await fetch(`${apiUrl}/api/v1/auth/me?token=${token}`);
        
        if (response.ok) {
          const data = await response.json();
          setUserData(data);
        } else {
          localStorage.removeItem('loki_token');
          localStorage.removeItem('loki_user');
          router.push('/auth');
        }
      } catch (error) {
        console.error('Error cargando datos:', error);
      } finally {
        setLoading(false);
      }
    };

    const token = localStorage.getItem('loki_token');
    if (!token) {
      router.push('/auth');
      return;
    }

    loadUserData(token);
  }, [router]);

  const handleLogout = () => {
    localStorage.removeItem('loki_token');
    localStorage.removeItem('loki_user');
    router.push('/');
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-linear-to-br from-purple-50 to-pink-50">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-600"></div>
      </div>
    );
  }

  if (!userData) {
    return null;
  }

  const moods = userData.moods || [];
  const avgMood = moods.length > 0
    ? (moods.reduce((sum, m) => sum + m.nivel, 0) / moods.length).toFixed(1)
    : 'N/A';

  // Calcular días activo (asegurarse de que no sea negativo)
  const daysActive = userData.fecha_registro
    ? Math.max(0, Math.floor((Date.now() - new Date(userData.fecha_registro).getTime()) / (1000 * 60 * 60 * 24)))
    : 0;

  const trustLevel = userData.trust_level || {
    nivel_confianza: 1,
    total_interacciones: 0,
    nivel_nombre: "Conociendo",
    mensajes_hasta_siguiente_nivel: 10
  };

  const weeklyTrend = [
    { day: 'Lun', mood: 7, activities: 3 },
    { day: 'Mar', mood: 6, activities: 2 },
    { day: 'Mié', mood: 8, activities: 4 },
    { day: 'Jue', mood: 7, activities: 3 },
    { day: 'Vie', mood: 9, activities: 5 },
    { day: 'Sáb', mood: 8, activities: 4 },
    { day: 'Dom', mood: 7, activities: 2 },
  ];

  const getMoodEmoji = (mood: number) => {
    if (mood >= 9) return '😄';
    if (mood >= 7) return '😊';
    if (mood >= 5) return '😐';
    if (mood >= 3) return '😔';
    return '😢';
  };

  const getMoodColor = (mood: number) => {
    if (mood >= 8) return 'text-green-600';
    if (mood >= 6) return 'text-blue-600';
    if (mood >= 4) return 'text-yellow-600';
    return 'text-red-600';
  };

  return (
    <div className="min-h-screen bg-linear-to-br from-purple-50 via-pink-50 to-orange-50">
      <header className="bg-white border-b border-gray-200 sticky top-0 z-10 shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <div className="w-10 h-10 bg-linear-to-br from-purple-500 to-pink-500 rounded-full flex items-center justify-center">
                <span className="text-2xl">🤖</span>
              </div>
              <div>
                <h1 className="text-2xl font-bold text-gray-900">Loki Dashboard</h1>
                <p className="text-sm text-gray-600">Tu compañero de bienestar emocional</p>
              </div>
            </div>
            <button
              onClick={handleLogout}
              className="px-4 py-2 text-sm font-medium text-gray-700 hover:text-gray-900 hover:bg-gray-100 rounded-lg transition-colors"
            >
              Cerrar sesión
            </button>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="mb-8 bg-linear-to-r from-purple-600 to-pink-600 rounded-2xl p-8 text-white shadow-lg">
          <h2 className="text-3xl font-bold mb-2">
            ¡Hola, {userData.nombre}! 👋
          </h2>
          <p className="text-purple-100 text-lg">
            Bienvenido a tu dashboard personal de bienestar emocional
          </p>
          <div className="mt-4 flex items-center space-x-2">
            <Badge className="bg-white/20 text-white border-white/30 hover:bg-white/30">
              Nivel de confianza: {trustLevel.nivel_nombre}
            </Badge>
            <Badge className="bg-white/20 text-white border-white/30 hover:bg-white/30">
              {trustLevel.total_interacciones} conversaciones
            </Badge>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <Card className="hover:shadow-lg transition-shadow">
            <CardHeader className="pb-3">
              <CardDescription>Estado promedio</CardDescription>
              <CardTitle className={`text-4xl ${typeof avgMood === 'number' ? getMoodColor(parseFloat(avgMood)) : 'text-gray-400'}`}>
                {avgMood}
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex items-center justify-between">
                <p className="text-sm text-gray-600">Últimos 30 días</p>
                <span className="text-3xl">📊</span>
              </div>
            </CardContent>
          </Card>

          <Card className="hover:shadow-lg transition-shadow">
            <CardHeader className="pb-3">
              <CardDescription>Registros totales</CardDescription>
              <CardTitle className="text-4xl text-blue-600">{moods.length}</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex items-center justify-between">
                <p className="text-sm text-gray-600">Entradas guardadas</p>
                <span className="text-3xl">📝</span>
              </div>
            </CardContent>
          </Card>

          <Card className="hover:shadow-lg transition-shadow">
            <CardHeader className="pb-3">
              <CardDescription>Días activo</CardDescription>
              <CardTitle className="text-4xl text-orange-600">{daysActive}</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex items-center justify-between">
                <p className="text-sm text-gray-600">Desde que te registraste</p>
                <span className="text-3xl">🔥</span>
              </div>
            </CardContent>
          </Card>

          <Card className="hover:shadow-lg transition-shadow bg-linear-to-br from-purple-50 to-pink-50 border-purple-200">
            <CardHeader className="pb-3">
              <CardDescription>Nivel de confianza</CardDescription>
              <CardTitle className="text-4xl text-purple-600">{trustLevel.nivel_confianza}/5</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex items-center justify-between">
                <p className="text-sm text-gray-600">{trustLevel.nivel_nombre}</p>
                <span className="text-3xl">🤝</span>
              </div>
              {!trustLevel.es_nivel_maximo && trustLevel.mensajes_hasta_siguiente_nivel > 0 && (
                <div className="mt-2">
                  <div className="w-full bg-purple-200 rounded-full h-2">
                    <div
                      className="bg-purple-600 h-2 rounded-full transition-all"
                      style={{
                        width: `${Math.min(100, ((10 - trustLevel.mensajes_hasta_siguiente_nivel) / 10) * 100)}%`
                      }}
                    ></div>
                  </div>
                  <p className="text-xs text-gray-500 mt-1">
                    {trustLevel.mensajes_hasta_siguiente_nivel} mensajes para siguiente nivel
                  </p>
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
          <Card>
            <CardHeader>
              <CardTitle>Tendencia de ánimo</CardTitle>
              <CardDescription>Últimos 7 días</CardDescription>
            </CardHeader>
            <CardContent>
              <MoodTrendChart data={weeklyTrend} />
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Actividades completadas</CardTitle>
              <CardDescription>Hábitos y check-ins semanales</CardDescription>
            </CardHeader>
            <CardContent>
              <ActivitiesChart data={weeklyTrend} />
            </CardContent>
          </Card>
        </div>

        {moods.length > 0 && (
          <Card className="mb-8">
            <CardHeader>
              <CardTitle>Registro reciente de estados</CardTitle>
              <CardDescription>Tus últimas entradas emocionales</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {moods.slice(-5).reverse().map((mood, index) => (
                  <div key={index} className="flex items-center justify-between p-4 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors">
                    <div className="flex items-center space-x-4">
                      <span className="text-3xl">{getMoodEmoji(mood.nivel)}</span>
                      <div>
                        <p className="font-medium text-gray-900">Nivel: {mood.nivel}/10</p>
                        <p className="text-sm text-gray-600">
                          {new Date(mood.timestamp).toLocaleDateString('es-ES', { 
                            weekday: 'long', 
                            year: 'numeric', 
                            month: 'long', 
                            day: 'numeric' 
                          })}
                        </p>
                      </div>
                    </div>
                    {mood.notas_texto && (
                      <Badge variant="outline" className="max-w-xs truncate">
                        {mood.notas_texto}
                      </Badge>
                    )}
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        )}

        <Card className="bg-linear-to-br from-purple-100 to-pink-100 border-purple-200">
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <span>🚧</span>
              <span>Próximamente</span>
            </CardTitle>
            <CardDescription>
              Funciones en desarrollo para mejorar tu experiencia
            </CardDescription>
          </CardHeader>
          <CardContent>
            <ul className="space-y-2">
              <li className="flex items-center space-x-2">
                <Badge>📈</Badge>
                <span>Análisis de patrones emocionales con IA</span>
              </li>
              <li className="flex items-center space-x-2">
                <Badge>💬</Badge>
                <span>Historial completo de conversaciones</span>
              </li>
              <li className="flex items-center space-x-2">
                <Badge>🎯</Badge>
                <span>Seguimiento de objetivos y hábitos</span>
              </li>
              <li className="flex items-center space-x-2">
                <Badge>📊</Badge>
                <span>Reportes mensuales personalizados</span>
              </li>
            </ul>
          </CardContent>
        </Card>

        <div className="mt-8 text-center text-gray-600">
          <p className="mb-2">Sigue usando Loki por WhatsApp para generar más datos 💬</p>
          <a 
            href="https://wa.me/14155238886?text=Hola%20Loki" 
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center space-x-2 px-6 py-3 bg-green-500 hover:bg-green-600 text-white font-medium rounded-lg transition-colors"
          >
            <span>💬</span>
            <span>Abrir WhatsApp</span>
          </a>
        </div>
      </main>
    </div>
  );
}
