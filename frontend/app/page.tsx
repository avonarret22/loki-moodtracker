export default function Home() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-600 via-pink-500 to-orange-400">
      <div className="container mx-auto px-4 py-16">
        <div className="max-w-4xl mx-auto text-center text-white">
          {/* Logo/Hero */}
          <div className="mb-8">
            <div className="w-32 h-32 bg-white/20 backdrop-blur-lg rounded-full mx-auto flex items-center justify-center mb-6">
              <span className="text-7xl">🤖</span>
            </div>
            <h1 className="text-6xl font-bold mb-4">Loki</h1>
            <p className="text-2xl text-purple-100 mb-8">
              Tu compañero de bienestar emocional vía WhatsApp
            </p>
          </div>

          {/* Features */}
          <div className="grid md:grid-cols-3 gap-8 mb-12">
            <div className="bg-white/10 backdrop-blur-lg rounded-2xl p-6">
              <span className="text-5xl block mb-4">📊</span>
              <h3 className="text-xl font-semibold mb-2">Tracking Emocional</h3>
              <p className="text-purple-100">
                Registra tu estado de ánimo cada día y descubre patrones
              </p>
            </div>

            <div className="bg-white/10 backdrop-blur-lg rounded-2xl p-6">
              <span className="text-5xl block mb-4">💬</span>
              <h3 className="text-xl font-semibold mb-2">IA Empática</h3>
              <p className="text-purple-100">
                Conversaciones inteligentes que te entienden y apoyan
              </p>
            </div>

            <div className="bg-white/10 backdrop-blur-lg rounded-2xl p-6">
              <span className="text-5xl block mb-4">💪</span>
              <h3 className="text-xl font-semibold mb-2">Hábitos Saludables</h3>
              <p className="text-purple-100">
                Construye rutinas positivas con recordatorios personalizados
              </p>
            </div>
          </div>

          {/* CTA */}
          <div className="bg-white/10 backdrop-blur-lg rounded-2xl p-8 mb-8">
            <h2 className="text-3xl font-bold mb-4">¿Cómo empezar?</h2>
            <ol className="text-left max-w-md mx-auto space-y-4 text-lg">
              <li className="flex items-start">
                <span className="text-2xl mr-3">1️⃣</span>
                <span>Envía un mensaje de WhatsApp a <strong>+1 415 523 8886</strong></span>
              </li>
              <li className="flex items-start">
                <span className="text-2xl mr-3">2️⃣</span>
                <span>Escribe: <code className="bg-white/20 px-2 py-1 rounded">join pictured-certainly</code></span>
              </li>
              <li className="flex items-start">
                <span className="text-2xl mr-3">3️⃣</span>
                <span>¡Empieza a chatear con Loki!</span>
              </li>
            </ol>
          </div>

          {/* Dashboard Access */}
          <div className="bg-white/10 backdrop-blur-lg rounded-2xl p-6">
            <p className="text-lg mb-2">
              ¿Ya usas Loki? Solicita tu dashboard escribiendo:
            </p>
            <code className="bg-white/20 px-4 py-2 rounded-lg text-xl">
              dashboard
            </code>
          </div>
        </div>
      </div>
    </div>
  );
}
