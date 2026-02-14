'use client';

import React, { Suspense, useEffect, useState } from 'react';
import Link from 'next/link';
import { ArrowLeft } from 'lucide-react';
import { useSearchParams } from 'next/navigation';
import { CheckInButton } from '@/components/CheckInButton';
import { TipButton } from '@/components/TipButton';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

interface Event {
  id: number;
  title: string;
  date: string;
  venue?: string;
  support_wallet?: string;
}

const MONTHS = [
  'ene',
  'feb',
  'mar',
  'abr',
  'may',
  'jun',
  'jul',
  'ago',
  'sep',
  'oct',
  'nov',
  'dic',
];

const formatFullDate = (value: string) => {
  if (!value) {
    return '';
  }
  const [year, month, day] = value.split('-').map(Number);
  if (!year || !month || !day) {
    return value;
  }
  const label = MONTHS[month - 1] || '';
  return `${String(day).padStart(2, '0')} ${label} ${year}`;
};

function CheckInContent() {
  const searchParams = useSearchParams();
  const eventIdParam = searchParams.get('event_id');
  const eventId = eventIdParam ? Number(eventIdParam) : NaN;
  const [event, setEvent] = useState<Event | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!eventIdParam || Number.isNaN(eventId)) {
      setError('Missing event_id');
      return;
    }
    setLoading(true);
    fetch(`${API_BASE}/api/events/${eventId}`)
      .then((res) => {
        if (!res.ok) {
          throw new Error('Event not found');
        }
        return res.json();
      })
      .then((data) => {
        setEvent(data);
        setError(null);
      })
      .catch((err) => setError(err.message || 'Failed to load event'))
      .finally(() => setLoading(false));
  }, [eventId, eventIdParam]);

  return (
    <main className="max-w-3xl mx-auto px-6 py-10">
      <div className="nb-card nb-card-static p-8 bg-[#1a1a1a]">
        <div className="flex items-center justify-between gap-4 mb-6">
          <h1 className="text-4xl font-black uppercase tracking-tight">Event Check-in</h1>
          <Link
            href="/"
            className="nb-button bg-black text-[#a1ff00] border-2 border-[#a1ff00] px-4 py-2 text-xs font-black uppercase flex items-center gap-2"
          >
            <ArrowLeft size={14} />
            Back
          </Link>
        </div>
        
        {loading && <p className="font-bold animate-pulse text-[#a1ff00]">Loading event details...</p>}
        {error && <p className="text-red-400 font-bold border-2 border-red-400 p-4 bg-red-400/10 mb-4">{error}</p>}
        
        {event && (
          <div className="mb-8 border-b-2 border-white/10 pb-6">
            <div className="text-2xl font-black uppercase mb-1 italic leading-none">{event.title}</div>
            <div className="text-[#a1ff00] font-black text-sm uppercase">
              {formatFullDate(event.date)}{event.venue ? ` • ${event.venue}` : ''}
            </div>
          </div>
        )}

        <div className="border-2 border-white p-6 mb-10 text-sm font-bold leading-relaxed bg-black/30">
          <div className="text-[10px] uppercase font-black mb-3 tracking-widest text-[#a1ff00]">Why check-in?</div>
          <ul className="list-disc pl-5 space-y-2 text-white/90">
            <li>Get access to photos, videos, or a playlist after the event.</li>
            <li>Unlock perks or discounts for future events.</li>
            <li>Join private chats or afterparty invites.</li>
            <li>Help artists show real attendance (less spam, more trust).</li>
            <li>Your check-in is private and not posted on the blockchain.</li>
          </ul>
        </div>

        {!loading && !error && event && (
          <div className="space-y-8">
            <div className="space-y-4">
              <div className="text-[10px] font-black uppercase text-white/40 tracking-wider">Support the artist</div>
              <TipButton 
                walletAddress={event.support_wallet || ""} 
                artistName={event.title.split(' - ')[0]} 
              />
              <CheckInButton eventId={event.id} />
            </div>
            
            <div className="border-2 border-white/20 bg-black/20 p-3 text-center">
              <span className="text-[10px] font-black uppercase text-white/50 tracking-widest">
                Private check-in (Not on blockchain)
              </span>
            </div>
          </div>
        )}
      </div>
    </main>
  );
}

export default function CheckInPage() {
  return (
    <Suspense
      fallback={
        <main className="max-w-3xl mx-auto px-6 py-10">
          <div className="nb-card p-8 bg-[#1a1a1a]">
            <p className="font-bold animate-pulse text-[#a1ff00]">Loading event details...</p>
          </div>
        </main>
      }
    >
      <CheckInContent />
    </Suspense>
  );
}
