'use client';

import React, { Suspense, useEffect, useState } from 'react';
import { useSearchParams } from 'next/navigation';
import { CheckCircle, XCircle, Search, ShieldCheck, MapPin, Calendar } from 'lucide-react';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

function VerifyContent() {
  const searchParams = useSearchParams();
  const eventId = searchParams.get('event_id');
  const address = searchParams.get('wallet_address');
  
  const [status, setStatus] = useState<'loading' | 'verified' | 'invalid' | 'error'>('loading');
  const [eventData, setEventData] = useState<any>(null);
  const [checkinDetails, setCheckinDetails] = useState<any>(null);

  useEffect(() => {
    if (!eventId || !address) {
      setStatus('invalid');
      return;
    }

    const verify = async () => {
      try {
        // 1. Fetch event details
        const eventRes = await fetch(`${API_BASE}/api/events/${eventId}`);
        if (eventRes.ok) {
          setEventData(await eventRes.json());
        }

        // 2. Fetch check-in status
        const res = await fetch(`${API_BASE}/api/checkin/status?event_id=${eventId}&wallet_address=${address.toLowerCase()}`);
        if (!res.ok) {
          setStatus('invalid');
          return;
        }

        const data = await res.json();
        if (data.status === 'checked_in') {
          setStatus('verified');
          setCheckinDetails(data);
        } else {
          setStatus('invalid');
        }
      } catch (err) {
        console.error(err);
        setStatus('error');
      }
    };

    verify();
  }, [eventId, address]);

  return (
    <main className="min-h-screen bg-black flex flex-col items-center justify-center p-6">
      <div className={`nb-card w-full max-w-md p-8 nb-card-static ${
        status === 'verified' ? 'bg-[#a1ff00] text-black border-black shadow-[8px_8px_0px_0px_#ffffff]' : 
        status === 'invalid' ? 'bg-red-500 text-white border-white shadow-[8px_8px_0px_0px_#000000]' : 
        'bg-[#1a1a1a] text-white'
      }`}>
        
        <div className="flex items-center gap-3 mb-8 border-b-4 border-current pb-6">
          <ShieldCheck size={32} />
          <h1 className="text-3xl font-black uppercase italic tracking-tighter">
            Vibe Proof
          </h1>
        </div>

        {status === 'loading' && (
          <div className="flex flex-col items-center py-10">
            <Search size={48} className="animate-bounce mb-4" />
            <p className="font-black uppercase tracking-widest animate-pulse">Verifying Check-in...</p>
          </div>
        )}

        {status === 'verified' && (
          <div className="animate-in zoom-in-95 duration-500">
            <div className="flex items-center gap-4 mb-6">
              <CheckCircle size={64} className="fill-black" />
              <div>
                <div className="text-4xl font-black uppercase leading-none">Verified</div>
                <div className="text-xs font-bold uppercase tracking-widest opacity-70">Entry Approved</div>
              </div>
            </div>

            <div className="space-y-4 bg-black/10 p-4 border-2 border-black/20 font-bold uppercase text-sm">
              {eventData && (
                <>
                  <div className="flex items-start gap-2">
                    <MapPin size={16} className="mt-1" />
                    <span>{eventData.title}</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <Calendar size={16} />
                    <span>{eventData.date}</span>
                  </div>
                </>
              )}
              <div className="pt-2 border-t border-black/20 text-[10px] font-mono break-all opacity-60">
                WHET: {address}
              </div>
              {checkinDetails?.created_at && (
                <div className="text-[10px] opacity-60">
                  SIGNED: {new Date(checkinDetails.created_at).toLocaleString()}
                </div>
              )}
            </div>
          </div>
        )}

        {status === 'invalid' && (
          <div className="text-center py-10">
            <XCircle size={64} className="mx-auto mb-4" />
            <h2 className="text-3xl font-black uppercase mb-2">Invalid Proof</h2>
            <p className="font-bold opacity-80 uppercase text-xs">This check-in was not found or is forged.</p>
          </div>
        )}

        {status === 'error' && (
          <div className="text-center py-10">
            <p className="font-black uppercase text-red-400">System Error</p>
            <p className="text-xs opacity-60 mt-2">Failed to reach the Vibe Oracle.</p>
          </div>
        )}
      </div>

      <button 
        onClick={() => window.location.href = '/'}
        className="mt-12 text-white/40 font-black uppercase text-[10px] tracking-[0.2em] hover:text-white transition-colors"
      >
        ← Back to BA Nightlife
      </button>
    </main>
  );
}

export default function VerifyPage() {
  return (
    <Suspense fallback={<div className="min-h-screen bg-black" />}>
      <VerifyContent />
    </Suspense>
  );
}
