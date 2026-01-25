'use client';

import React, { useEffect, useState } from "react";
import { Music, MapPin, Calendar, ExternalLink, Sparkles } from "lucide-react";
import { ConnectButton } from '@rainbow-me/rainbowkit';
import { TipButton } from "@/components/TipButton";

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

export default function Home() {
  const [events, setEvents] = useState<Event[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch('http://localhost:8000/api/events')
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
      const res = await fetch(`http://localhost:8000/api/scrape/${source}`, { method: 'POST' });
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
    <main className="max-w-7xl mx-auto px-4 py-8 bg-white min-h-screen">
      {/* Header with Wallet Connect */}
      <div className="flex justify-between items-center mb-16">
        <div className="bg-black text-white px-6 py-2 border-4 border-black font-black text-xl uppercase tracking-tighter">
          BA NIGHTLIFE
        </div>
        <div className="nb-button px-4 py-1">
          <ConnectButton label="CONNECT WALLET" />
        </div>
      </div>

      <div className="flex flex-col items-center mb-24 text-center">
        <h1 className="text-8xl md:text-9xl font-black mb-6 tracking-tighter uppercase leading-none italic">
          <span className="bg-[#a1ff00] px-4 border-4 border-black nb-title">Music</span><br/>
          <span className="bg-[#ff3cff] px-4 border-4 border-black nb-title text-white">Events</span>
        </h1>
        <p className="text-2xl font-bold bg-[#ffdb00] px-6 py-2 border-4 border-black -rotate-1 mt-4">
          BUENOS AIRES UNDERGROUND SCENE
        </p>
      </div>

      {loading ? (
        <div className="flex justify-center items-center h-64">
          <div className="animate-bounce bg-black text-white p-6 border-4 border-black font-black text-3xl">
            LOADING EVENTS...
          </div>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-12">
          {events.length > 0 ? events.map((event) => (
            <div key={event.id} className="nb-card flex flex-col group">
              <div className="h-64 border-b-4 border-black relative overflow-hidden">
                {event.media_url ? (
                  <img src={event.media_url} alt={event.title} className="w-full h-full object-cover grayscale group-hover:grayscale-0 transition-all" />
                ) : (
                  <div className="w-full h-full bg-[#ff3cff]" />
                )}
                <div className="absolute top-4 right-4 bg-black text-white px-4 py-1 font-black text-xs uppercase border-2 border-white">
                  {event.genres?.[0] || 'RAVE'}
                </div>
              </div>
              <div className="p-8 flex-1 flex flex-col bg-white">
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

                {/* AI Vibe Section */}
                {event.vibe_description && (
                  <div className="mb-6 p-4 bg-gray-100 border-2 border-black flex flex-col relative">
                    <div className="absolute -top-3 left-4 bg-black text-[#a1ff00] px-2 text-xs font-black uppercase tracking-widest flex items-center border border-black transform -rotate-1">
                      <Sparkles size={12} className="mr-1" />
                      AI Vibe Match
                    </div>
                    <p className="text-sm font-bold italic leading-relaxed text-gray-800 mt-1">
                      "{event.vibe_description}"
                    </p>
                  </div>
                )}
                
                <div className="mt-auto flex flex-col gap-4">
                  <a 
                    href={event.source_link} 
                    target="_blank" 
                    className="nb-button text-center py-4 text-lg"
                  >
                    GET TICKETS
                  </a>
                  
                  {/* Web3 Tipping Feature */}
                  <TipButton 
                    walletAddress={event.support_wallet || ""} 
                    artistName={event.title.split(' - ')[0]} 
                  />
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

      {/* Admin / Scraper Triggers */}
      <section className="mt-24 border-4 border-dashed border-gray-400 p-8">
        <h2 className="text-2xl font-black uppercase mb-6 text-gray-400">Admin Control Panel</h2>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
           {['venti', 'passline', 'catpass', 'bombo'].map(source => (
             <button 
               key={source}
               onClick={() => refreshScraper(source)}
               className="bg-gray-200 hover:bg-gray-300 border-2 border-black font-bold py-2 uppercase tracking-wide"
             >
               Refresh {source}
             </button>
           ))}
        </div>
      </section>

      <footer className="mt-32 border-t-8 border-black py-12 flex justify-between items-center bg-black text-white px-8">
        <div className="font-black text-2xl italic uppercase tracking-tighter">BA NIGHTLIFE // 2026</div>
        <div className="flex gap-8 font-bold uppercase underline decoration-2 underline-offset-4">
          <span>Telegram</span>
          <span>BNB Chain</span>
          <span>N8N</span>
        </div>
      </footer>
    </main>
  );
}
