'use client';

import React, { useEffect, useState } from 'react';
import { QRCodeCanvas } from 'qrcode.react';
import { LayoutGrid, QrCode, X } from 'lucide-react';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

interface Event {
  id: number;
  title: string;
  date: string;
  venue?: string;
}

export default function AdminPage() {
  const [events, setEvents] = useState<Event[]>([]);
  const [selectedEvent, setSelectedEvent] = useState<Event | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch(`${API_BASE}/api/events?limit=50`)
      .then((res) => res.json())
      .then((data) => {
        setEvents(data.events || []);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, []);

  const qrUrl = selectedEvent 
    ? `${window.location.origin}/checkin?event_id=${selectedEvent.id}&source=admin`
    : '';

  return (
    <main className="min-h-screen bg-black text-white p-8">
      <div className="max-w-6xl mx-auto">
        <header className="mb-12 flex items-center justify-between border-b-4 border-white pb-6">
          <h1 className="text-5xl font-black uppercase tracking-tighter">
            Staff Panel <span className="text-[#a1ff00]">/ QR Desk</span>
          </h1>
          <LayoutGrid className="text-white/20" size={48} />
        </header>

        {loading ? (
          <p className="text-2xl font-black animate-pulse text-[#a1ff00]">Loading events...</p>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {events.map((event) => (
              <button
                key={event.id}
                onClick={() => setSelectedEvent(event)}
                className="nb-card p-6 bg-[#1a1a1a] border-2 border-white hover:border-[#a1ff00] transition-colors text-left group"
              >
                <div className="text-[10px] uppercase font-black text-white/40 mb-2 truncate">
                  {event.id} // {event.date}
                </div>
                <div className="text-xl font-black uppercase group-hover:text-[#a1ff00] transition-colors line-clamp-2">
                  {event.title}
                </div>
              </button>
            ))}
          </div>
        )}

        {selectedEvent && (
          <div className="fixed inset-0 bg-black/95 z-50 flex items-center justify-center p-6 animate-in fade-in duration-300">
            <div className="nb-card bg-white p-12 max-w-2xl w-full flex flex-col items-center relative border-8 border-black shadow-[20px_20px_0px_0px_#a1ff00]">
              <button 
                onClick={() => setSelectedEvent(null)}
                className="absolute top-4 right-4 text-black hover:bg-black hover:text-white p-2 border-4 border-black transition-colors"
              >
                <X size={32} />
              </button>

              <div className="text-black font-black uppercase text-center mb-8">
                <div className="text-sm tracking-widest opacity-50 mb-2">Scan to Check-In</div>
                <h2 className="text-4xl leading-none">{selectedEvent.title}</h2>
              </div>

              <div className="bg-white p-4 border-8 border-black mb-8">
                <QRCodeCanvas 
                  value={qrUrl} 
                  size={320}
                  level="H"
                  includeMargin={false}
                />
              </div>

              <p className="text-black/30 font-mono text-[10px] break-all max-w-sm text-center mb-0">
                {qrUrl}
              </p>
              
              <div className="mt-8 flex items-center gap-4 bg-black text-[#a1ff00] px-8 py-4 border-4 border-black font-black uppercase italic">
                <QrCode size={24} />
                Desk QR Ready
              </div>
            </div>
          </div>
        )}
      </div>
    </main>
  );
}
