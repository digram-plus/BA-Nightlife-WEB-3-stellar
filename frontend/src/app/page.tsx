'use client';

import React, { useEffect, useState } from "react";
import { Music, MapPin, Calendar, ExternalLink, Sparkles } from "lucide-react";
import { ConnectButton } from '@rainbow-me/rainbowkit';
import { TipButton } from "@/components/TipButton";
import { CheckInButton } from "@/components/CheckInButton";

interface Event {
  id: number;
  title: string;
  date: string;
  venue: string;
  genres: string[];
  source_link: string;
  media_url?: string;
  support_wallet?: string;
  vibe_description?: string;
}

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export default function Home() {
  const [events, setEvents] = useState<Event[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch(`${API_BASE}/api/events`)
      .then(res => res.json())
      .then(data => {
        setEvents(data);
        setLoading(false);
      })
      .catch(err => {
        console.error("Failed to fetch events:", err);
        setLoading(false);
      });
  }, []);


  const refreshScraper = async (source: string) => {
    try {
      const res = await fetch(`/api/admin/scrape/${source}`, { method: 'POST' });
      if (res.ok) {
        alert(`Started scraping ${source}! Give it a few seconds/minutes.`);
      } else {
        alert(`Failed to start ${source}`);
      }
    } catch (e) {
      console.error(e);
      alert("Error contacting backend");
    }
  };

  return (
    <main className="max-w-7xl mx-auto px-4 py-8 bg-[#0a0a0a] min-h-screen text-white">
      {/* Header with Wallet Connect */}
      <div className="flex justify-between items-center mb-16 px-2">
        <div className="flex items-center gap-4">
          <div className="w-16 h-16 bg-[#a1ff00] p-1 border-4 border-white shadow-[4px_4px_0px_0px_#ffffff]">
            <img src="/icon.png" alt="BA Nightlife Logo" className="w-full h-full object-contain" />
          </div>
          <div className="hidden md:block bg-black text-[#a1ff00] px-4 py-1 border-2 border-white font-black text-sm uppercase tracking-widest -rotate-1">
            EST. 2026
          </div>
        </div>
        <div className="nb-button">
          <ConnectButton label="CONNECT WALLET" showBalance={false} chainStatus="none" accountStatus="address" />
        </div>
      </div>

      <div className="flex flex-col items-center mb-24 text-center">
        <h1 className="text-8xl md:text-9xl font-black mb-6 tracking-tighter uppercase leading-none italic">
          <span className="bg-[#a1ff00] px-4 border-4 border-white nb-title text-black">Music</span><br/>
          <span className="bg-[#ff3cff] px-4 border-4 border-white nb-title text-white">Events</span>
        </h1>
        <p className="text-2xl font-bold bg-[#a1ff00] px-6 py-2 border-4 border-white rotate-1 mt-4 text-[#ff3cff] shadow-[6px_6px_0px_0px_#ffffff]">
          BUENOS AIRES UNDERGROUND SCENE
        </p>
      </div>

      {loading ? (
        <div className="flex justify-center items-center h-64">
          <div className="animate-bounce bg-white text-black p-6 border-4 border-white font-black text-3xl">
            LOADING EVENTS...
          </div>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-12">
          {events.length > 0 ? events.map((event) => (
            <div key={event.id} className="nb-card flex flex-col group">
              <div className="h-64 border-b-4 border-white relative overflow-hidden">
                {event.media_url ? (
                  <img src={event.media_url} alt={event.title} className="w-full h-full object-cover grayscale group-hover:grayscale-0 transition-all" />
                ) : (
                  <div className="w-full h-full bg-[#ff3cff]" />
                )}
                <div className="absolute top-4 right-4 bg-black text-white px-4 py-1 font-black text-xs uppercase border-2 border-white">
                  {event.genres?.[0] || 'RAVE'}
                </div>
              </div>
              <div className="p-8 flex-1 flex flex-col bg-[#1a1a1a]">
                <h3 className="text-3xl font-black mb-6 uppercase leading-tight line-clamp-2 italic">{event.title}</h3>
                
                <div className="space-y-4 mb-8">
                  <div className="flex items-center font-bold text-lg">
                    <Calendar size={20} className="mr-3 fill-[#a1ff00]" />
                    <span className="bg-black text-white px-3 py-0.5">{new Date(event.date).toLocaleDateString('es-AR', { day: '2-digit', month: 'short' })}</span>
                  </div>
                  <div className="flex items-center font-bold text-lg">
                    <MapPin size={20} className="mr-3 fill-[#ffdb00]" />
                    <span className="underline decoration-4 decoration-[#ff3cff]">{event.venue || 'BUENOS AIRES'}</span>
                  </div>
                </div>

                {/* AI Vibe "Sticker" Section */}
                {event.vibe_description && (
                  <div className="mb-8 p-5 bg-[#a1ff00] border-4 border-black text-black relative transform rotate-1 transition-all group-hover:-rotate-1 shadow-[4px_4px_0px_0px_#ffffff]">
                    {/* Retro Tape Effect */}
                    <div className="absolute -top-4 left-1/2 -translate-x-1/2 w-16 h-6 bg-white/40 border border-black/10 backdrop-blur-sm -rotate-2" />
                    
                    <div className="flex items-center gap-2 mb-2 font-black text-[10px] uppercase tracking-tighter opacity-70">
                      <Sparkles size={12} />
                      AI Vibe Oracle
                    </div>
                    <p className="text-sm font-black italic leading-tight">
                      "{event.vibe_description}"
                    </p>
                  </div>
                )}
                
                <div className="mt-auto flex flex-col gap-4">
                  <a 
                    href={event.source_link.startsWith('http') ? event.source_link : `https://${event.source_link}`} 
                    target="_blank" 
                    rel="noreferrer"
                    className="nb-button text-center py-4 text-lg"
                  >
                    GET TICKETS
                  </a>
                  
                  {/* Web3 Tipping & Proof Section */}
                  <TipButton 
                    walletAddress={event.support_wallet || ""} 
                    artistName={event.title.split(' - ')[0]} 
                  />

                  <CheckInButton eventId={event.id} />
                </div>
              </div>
            </div>
          )) : (
            <div className="col-span-full text-center py-24 nb-card bg-[#ffdb00]">
              <Music size={64} className="mx-auto mb-6" />
              <p className="text-4xl font-black uppercase">NO NOISE FOUND TODAY.</p>
            </div>
          )}
        </div>
      )}

      {/* Admin / Scraper Triggers (Restricted) */}
      {typeof window !== 'undefined' && window.location.search.includes('admin=true') && (
        <section className="mt-24 border-4 border-dashed border-gray-700 p-8">
          <h2 className="text-2xl font-black uppercase mb-6 text-gray-600">Admin Control Panel</h2>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
             {['venti', 'passline', 'catpass', 'bombo'].map(source => (
               <button 
                 key={source}
                 onClick={() => refreshScraper(source)}
                 className="nb-button bg-[#a1ff00] text-black py-3"
               >
                 Refresh {source}
               </button>
             ))}
          </div>
        </section>
      )}

      <footer className="mt-32 border-t-4 border-white py-12 flex justify-between items-center bg-black text-white px-8">
        <div className="font-black text-2xl italic uppercase tracking-tighter">BA NIGHTLIFE // 2026</div>
        <div className="flex gap-8 font-bold uppercase underline decoration-2 underline-offset-4 decoration-[#a1ff00]">
          <span>Telegram</span>
          <span>BNB Chain</span>
          <span>N8N</span>
        </div>
      </footer>
    </main>
  );
}
