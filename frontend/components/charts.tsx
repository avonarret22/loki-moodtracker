'use client';

import { AreaChart, Area, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

interface ChartData {
  day: string;
  mood: number;
  activities: number;
}

export function MoodTrendChart({ data }: { data: ChartData[] }) {
  return (
    <ResponsiveContainer width="100%" height={250}>
      <AreaChart data={data}>
        <defs>
          <linearGradient id="colorMood" x1="0" y1="0" x2="0" y2="1">
            <stop offset="5%" stopColor="#8b5cf6" stopOpacity={0.8}/>
            <stop offset="95%" stopColor="#8b5cf6" stopOpacity={0}/>
          </linearGradient>
        </defs>
        <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
        <XAxis dataKey="day" stroke="#6b7280" />
        <YAxis domain={[0, 10]} stroke="#6b7280" />
        <Tooltip 
          contentStyle={{ backgroundColor: '#fff', border: '1px solid #e5e7eb', borderRadius: '8px' }}
          labelStyle={{ color: '#374151', fontWeight: 'bold' }}
        />
        <Area 
          type="monotone" 
          dataKey="mood" 
          stroke="#8b5cf6" 
          strokeWidth={2}
          fillOpacity={1} 
          fill="url(#colorMood)" 
        />
      </AreaChart>
    </ResponsiveContainer>
  );
}

export function ActivitiesChart({ data }: { data: ChartData[] }) {
  return (
    <ResponsiveContainer width="100%" height={250}>
      <BarChart data={data}>
        <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
        <XAxis dataKey="day" stroke="#6b7280" />
        <YAxis stroke="#6b7280" />
        <Tooltip 
          contentStyle={{ backgroundColor: '#fff', border: '1px solid #e5e7eb', borderRadius: '8px' }}
          labelStyle={{ color: '#374151', fontWeight: 'bold' }}
        />
        <Bar 
          dataKey="activities" 
          fill="#ec4899" 
          radius={[8, 8, 0, 0]} 
        />
      </BarChart>
    </ResponsiveContainer>
  );
}
