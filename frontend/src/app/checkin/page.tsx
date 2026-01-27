'use client';

import React, { useEffect, useState } from 'react';
import { useSearchParams } from 'next/navigation';
import { CheckInButton } from '@/components/CheckInButton';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

interface Event {
  id: number;
  title: string;
  date: string;
  venue?: string;
}

export default function CheckInPage() {
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
      <div className="nb-card p-8">
        <h1 className="text-3xl font-black uppercase mb-4">Event Check-in</h1>
        {loading && <p className="font-bold">Loading event...</p>}
        {error && <p className="text-red-300 font-bold">{error}</p>}
        {event && (
          <div className="mb-6">
            <div className="text-xl font-black mb-2">{event.title}</div>
            <div className="text-sm font-bold">
              {new Date(event.date).toLocaleDateString('es-AR', {
                day: '2-digit',
                month: 'short',
                year: 'numeric',
              })}
              {event.venue ? ` • ${event.venue}` : ''}
            </div>
          </div>
        )}
        {!loading && !error && event && <CheckInButton eventId={event.id} />}
      </div>
    </main>
  );
}
