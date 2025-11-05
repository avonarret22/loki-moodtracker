'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import dynamic from 'next/dynamic';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { 
  TrendingUp, TrendingDown, Minus, Heart, MessageCircle, 
  Calendar, Award, Target, Sparkles, Brain, Activity
} from 'lucide-react';

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

interface WeeklyDataPoint {
  day: string;
  mood: number;
  activities: number;
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
  weekly_data?: WeeklyDataPoint[];
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
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-purple-50 to-pink-50">
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

  // Usar datos reales de la API o datos de ejemplo si no hay datos
  const weeklyTrend = userData.weekly_data && userData.weekly_data.length > 0
    ? userData.weekly_data
    : [
        { day: 'Lun', mood: 0, activities: 0 },
        { day: 'Mar', mood: 0, activities: 0 },
        { day: 'Mié', mood: 0, activities: 0 },
        { day: 'Jue', mood: 0, activities: 0 },
        { day: 'Vie', mood: 0, activities: 0 },
        { day: 'Sáb', mood: 0, activities: 0 },
        { day: 'Dom', mood: 0, activities: 0 },
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

  const getMoodTrend = () => {
    if (moods.length < 2) return { icon: Minus, text: 'Sin datos suficientes', color: 'text-gray-500' };
    
    const recent = moods.slice(-3).reduce((sum, m) => sum + m.nivel, 0) / Math.min(3, moods.length);
    const older = moods.slice(-7, -3).reduce((sum, m) => sum + m.nivel, 0) / Math.max(1, Math.min(4, moods.length - 3));
    
    if (recent > older + 1) return { icon: TrendingUp, text: 'Mejorando', color: 'text-green-600' };
    if (recent < older - 1) return { icon: TrendingDown, text: 'Bajando', color: 'text-red-600' };
    return { icon: Minus, text: 'Estable', color: 'text-blue-600' };
  };

  const moodTrend = getMoodTrend();
  const TrendIcon = moodTrend.icon;

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-50 via-pink-50 to-orange-50">
      <header className="bg-white border-b border-gray-200 sticky top-0 z-10 shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <div className="w-10 h-10 bg-gradient-to-br from-purple-500 to-pink-500 rounded-full flex items-center justify-center">
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
        <div className="mb-8 bg-gradient-to-r from-purple-600 to-pink-600 rounded-2xl p-8 text-white shadow-lg">
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
          {/* Card de Estado Promedio - MEJORADO */}
          <Card className="hover:shadow-xl transition-all duration-300 border-l-4 border-l-purple-500">
            <CardHeader className="pb-2">
              <div className="flex items-center justify-between">
                <CardDescription className="text-xs font-medium uppercase tracking-wide">Tu estado promedio</CardDescription>
                <Heart className="h-5 w-5 text-purple-500" />
              </div>
            </CardHeader>
            <CardContent>
              <div className="flex items-end justify-between">
                <div>
                  <div className={`text-5xl font-bold ${typeof avgMood === 'number' ? getMoodColor(parseFloat(avgMood)) : 'text-gray-400'}`}>
                    {avgMood}
                    <span className="text-2xl text-gray-400">/10</span>
                  </div>
                  <div className="flex items-center mt-2 space-x-2">
                    <TrendIcon className={`h-4 w-4 ${moodTrend.color}`} />
                    <span className={`text-sm font-medium ${moodTrend.color}`}>
                      {moodTrend.text}
                    </span>
                  </div>
                </div>
                <div className="text-5xl opacity-50">
                  {typeof avgMood === 'number' ? getMoodEmoji(parseFloat(avgMood)) : '📊'}
                </div>
              </div>
              <p className="text-xs text-gray-500 mt-3">Últimos 30 días</p>
            </CardContent>
          </Card>

          {/* Card de Registros Totales - MEJORADO */}
          <Card className="hover:shadow-xl transition-all duration-300 border-l-4 border-l-blue-500">
            <CardHeader className="pb-2">
              <div className="flex items-center justify-between">
                <CardDescription className="text-xs font-medium uppercase tracking-wide">Entradas registradas</CardDescription>
                <MessageCircle className="h-5 w-5 text-blue-500" />
              </div>
            </CardHeader>
            <CardContent>
              <div className="flex items-end justify-between">
                <div>
                  <div className="text-5xl font-bold text-blue-600">
                    {moods.length}
                  </div>
                  <p className="text-sm text-gray-600 mt-2">
                    {moods.length === 0 ? 'Aún sin registros' : 
                     moods.length === 1 ? 'Primera entrada' :
                     `+${Math.min(5, moods.length)} recientes`}
                  </p>
                </div>
                <div className="text-5xl opacity-50">📝</div>
              </div>
              <p className="text-xs text-gray-500 mt-3">Check-ins guardados</p>
            </CardContent>
          </Card>

          {/* Card de Días Activo - MEJORADO */}
          <Card className="hover:shadow-xl transition-all duration-300 border-l-4 border-l-orange-500">
            <CardHeader className="pb-2">
              <div className="flex items-center justify-between">
                <CardDescription className="text-xs font-medium uppercase tracking-wide">Racha activa</CardDescription>
                <Calendar className="h-5 w-5 text-orange-500" />
              </div>
            </CardHeader>
            <CardContent>
              <div className="flex items-end justify-between">
                <div>
                  <div className="text-5xl font-bold text-orange-600">
                    {daysActive}
                  </div>
                  <p className="text-sm text-gray-600 mt-2">
                    {daysActive === 0 ? '¡Bienvenido!' :
                     daysActive === 1 ? 'Primer día' :
                     daysActive < 7 ? 'Esta semana' :
                     daysActive < 30 ? 'Este mes' :
                     `${Math.floor(daysActive / 30)} meses`}
                  </p>
                </div>
                <div className="text-5xl opacity-50">🔥</div>
              </div>
              <p className="text-xs text-gray-500 mt-3">Desde {new Date(userData.fecha_registro).toLocaleDateString('es-ES', { month: 'short', year: 'numeric' })}</p>
            </CardContent>
          </Card>

          {/* Card de Nivel de Confianza - MEJORADO */}
          <Card className="hover:shadow-xl transition-all duration-300 border-l-4 border-l-purple-600 bg-gradient-to-br from-purple-50/50 to-pink-50/50">
            <CardHeader className="pb-2">
              <div className="flex items-center justify-between">
                <CardDescription className="text-xs font-medium uppercase tracking-wide">Nivel de confianza</CardDescription>
                <Award className="h-5 w-5 text-purple-600" />
              </div>
            </CardHeader>
            <CardContent>
              <div className="flex items-end justify-between">
                <div>
                  <div className="text-5xl font-bold text-purple-600">
                    {trustLevel.nivel_confianza}
                    <span className="text-2xl text-gray-400">/5</span>
                  </div>
                  <p className="text-sm font-semibold text-purple-700 mt-2">
                    {trustLevel.nivel_nombre}
                  </p>
                </div>
                <div className="text-5xl opacity-50">🤝</div>
              </div>
              {!trustLevel.es_nivel_maximo && trustLevel.mensajes_hasta_siguiente_nivel > 0 && (
                <div className="mt-4">
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-xs font-medium text-purple-700">Progreso</span>
                    <span className="text-xs text-gray-500">
                      {Math.max(0, 10 - trustLevel.mensajes_hasta_siguiente_nivel)}/10
                    </span>
                  </div>
                  <div className="w-full bg-purple-200 rounded-full h-2.5">
                    <div
                      className="bg-gradient-to-r from-purple-600 to-pink-600 h-2.5 rounded-full transition-all duration-500"
                      style={{
                        width: `${Math.min(100, ((10 - trustLevel.mensajes_hasta_siguiente_nivel) / 10) * 100)}%`
                      }}
                    ></div>
                  </div>
                  <p className="text-xs text-gray-500 mt-1.5">
                    {trustLevel.mensajes_hasta_siguiente_nivel} {trustLevel.mensajes_hasta_siguiente_nivel === 1 ? 'mensaje' : 'mensajes'} para subir
                  </p>
                </div>
              )}
              {trustLevel.es_nivel_maximo && (
                <div className="mt-3 flex items-center space-x-1">
                  <Sparkles className="h-4 w-4 text-yellow-500" />
                  <span className="text-xs font-medium text-purple-700">¡Nivel máximo!</span>
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        {/* SECCIÓN DE GRÁFICOS - MEJORADA */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
          <Card className="hover:shadow-lg transition-shadow">
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle className="flex items-center space-x-2">
                    <Activity className="h-5 w-5 text-purple-600" />
                    <span>Tendencia de ánimo</span>
                  </CardTitle>
                  <CardDescription className="mt-1">
                    Evolución de tus estados emocionales
                  </CardDescription>
                </div>
                {userData.weekly_data && userData.weekly_data.length > 0 && (
                  <Badge className="bg-green-100 text-green-800 border-green-300">
                    ✓ Datos reales
                  </Badge>
                )}
              </div>
            </CardHeader>
            <CardContent>
              <MoodTrendChart data={weeklyTrend} />
              {(!userData.weekly_data || userData.weekly_data.length === 0) && (
                <div className="mt-4 p-4 bg-orange-50 border border-orange-200 rounded-lg">
                  <p className="text-sm text-orange-800 font-medium">📊 Sin datos suficientes</p>
                  <p className="text-xs text-orange-600 mt-1">
                    Registra tu ánimo durante una semana para ver tendencias
                  </p>
                </div>
              )}
            </CardContent>
          </Card>

          <Card className="hover:shadow-lg transition-shadow">
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle className="flex items-center space-x-2">
                    <Target className="h-5 w-5 text-pink-600" />
                    <span>Actividades completadas</span>
                  </CardTitle>
                  <CardDescription className="mt-1">
                    Hábitos y check-ins realizados
                  </CardDescription>
                </div>
                {userData.weekly_data && userData.weekly_data.length > 0 && (
                  <Badge className="bg-green-100 text-green-800 border-green-300">
                    ✓ Datos reales
                  </Badge>
                )}
              </div>
            </CardHeader>
            <CardContent>
              <ActivitiesChart data={weeklyTrend} />
              {(!userData.weekly_data || userData.weekly_data.length === 0) && (
                <div className="mt-4 p-4 bg-orange-50 border border-orange-200 rounded-lg">
                  <p className="text-sm text-orange-800 font-medium">🎯 Sin actividades aún</p>
                  <p className="text-xs text-orange-600 mt-1">
                    Completa hábitos para ver tu progreso semanal
                  </p>
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        {/* REGISTROS RECIENTES - MEJORADO */}
        {moods.length > 0 && (
          <Card className="mb-8 border-t-4 border-t-purple-500">
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle className="flex items-center space-x-2">
                    <Brain className="h-5 w-5 text-purple-600" />
                    <span>Registro reciente de estados</span>
                  </CardTitle>
                  <CardDescription className="mt-1">
                    Tus últimas {Math.min(5, moods.length)} entradas emocionales
                  </CardDescription>
                </div>
                <Badge variant="outline" className="text-purple-700 border-purple-300">
                  {moods.length} total
                </Badge>
              </div>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {moods.slice(-5).reverse().map((mood, index) => (
                  <div 
                    key={index} 
                    className="group flex items-center justify-between p-4 bg-gradient-to-r from-gray-50 to-white rounded-xl hover:from-purple-50 hover:to-pink-50 transition-all duration-300 border border-gray-200 hover:border-purple-300 hover:shadow-md"
                  >
                    <div className="flex items-center space-x-4">
                      <div className="text-4xl group-hover:scale-110 transition-transform">
                        {getMoodEmoji(mood.nivel)}
                      </div>
                      <div>
                        <div className="flex items-center space-x-2">
                          <span className={`text-2xl font-bold ${getMoodColor(mood.nivel)}`}>
                            {mood.nivel}
                          </span>
                          <span className="text-sm text-gray-400">/10</span>
                        </div>
                        <p className="text-sm text-gray-600 mt-0.5">
                          {new Date(mood.timestamp).toLocaleDateString('es-ES', { 
                            weekday: 'short', 
                            day: 'numeric',
                            month: 'short',
                            hour: '2-digit',
                            minute: '2-digit'
                          })}
                        </p>
                      </div>
                    </div>
                    {mood.notas_texto && (
                      <div className="max-w-xs">
                        <Badge variant="outline" className="bg-white text-gray-700 border-gray-300 px-3 py-1">
                          💭 {mood.notas_texto.length > 40 
                            ? mood.notas_texto.substring(0, 40) + '...' 
                            : mood.notas_texto}
                        </Badge>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        )}

        {/* PRÓXIMAS FUNCIONES - MEJORADO */}
        <Card className="bg-gradient-to-br from-purple-50 via-pink-50 to-orange-50 border-2 border-purple-200 mb-8">
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <Sparkles className="h-6 w-6 text-purple-600" />
              <span className="text-purple-900">Próximamente</span>
            </CardTitle>
            <CardDescription>
              Nuevas funciones en desarrollo para mejorar tu experiencia
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="flex items-start space-x-3 p-3 bg-white/60 rounded-lg border border-purple-200">
                <div className="text-2xl">📈</div>
                <div>
                  <h4 className="font-semibold text-gray-900">Análisis de patrones</h4>
                  <p className="text-xs text-gray-600 mt-1">IA detectará tus patrones emocionales y te dará insights personalizados</p>
                </div>
              </div>
              <div className="flex items-start space-x-3 p-3 bg-white/60 rounded-lg border border-pink-200">
                <div className="text-2xl">💬</div>
                <div>
                  <h4 className="font-semibold text-gray-900">Historial completo</h4>
                  <p className="text-xs text-gray-600 mt-1">Revisa todas tus conversaciones con Loki desde el principio</p>
                </div>
              </div>
              <div className="flex items-start space-x-3 p-3 bg-white/60 rounded-lg border border-orange-200">
                <div className="text-2xl">🎯</div>
                <div>
                  <h4 className="font-semibold text-gray-900">Seguimiento de objetivos</h4>
                  <p className="text-xs text-gray-600 mt-1">Define metas y visualiza tu progreso hacia ellas</p>
                </div>
              </div>
              <div className="flex items-start space-x-3 p-3 bg-white/60 rounded-lg border border-blue-200">
                <div className="text-2xl">📊</div>
                <div>
                  <h4 className="font-semibold text-gray-900">Reportes mensuales</h4>
                  <p className="text-xs text-gray-600 mt-1">Recibe resúmenes automáticos de tu bienestar emocional</p>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* FOOTER CTA - MEJORADO */}
        <div className="text-center">
          <div className="bg-gradient-to-r from-green-50 to-emerald-50 rounded-2xl p-8 border-2 border-green-200">
            <div className="max-w-2xl mx-auto">
              <div className="text-5xl mb-4">💚</div>
              <h3 className="text-2xl font-bold text-gray-900 mb-2">
                Sigue tu camino hacia el bienestar
              </h3>
              <p className="text-gray-600 mb-6">
                Usa Loki por WhatsApp todos los días para generar más insights sobre tu salud emocional
              </p>
              <a 
                href="https://wa.me/14155238886?text=Hola%20Loki" 
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center space-x-3 px-8 py-4 bg-gradient-to-r from-green-500 to-emerald-600 hover:from-green-600 hover:to-emerald-700 text-white font-semibold rounded-xl transition-all duration-300 shadow-lg hover:shadow-xl transform hover:scale-105"
              >
                <MessageCircle className="h-5 w-5" />
                <span>Abrir chat con Loki</span>
              </a>
              <p className="text-xs text-gray-500 mt-4">
                Tus datos están seguros y son privados 🔒
              </p>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
