'use client';

import React, { useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import { Music, MapPin, Calendar, ExternalLink, Sparkles } from "lucide-react";
import { ConnectButton } from '@rainbow-me/rainbowkit';
import { CombinedConnectButton } from '@/components/CombinedConnectButton';
import { OpenfortButton } from '@openfort/react';

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
  const [selectedTags, setSelectedTags] = useState<Set<string>>(new Set());
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('asc');
  const [currentPage, setCurrentPage] = useState(1);
  const router = useRouter();

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

  const formatEventDate = (value: string) => {
    if (!value) {
      return '';
    }
    const d = new Date(value);
    if (isNaN(d.getTime())) {
      return value;
    }
    return d.toLocaleDateString('es-AR', { 
      day: '2-digit', 
      month: 'long', 
      year: 'numeric' 
    });
  };

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

  useEffect(() => {
    setCurrentPage(1);
  }, [selectedTags, sortOrder]);

  const tags = useMemo(() => {
    const values = new Set<string>();
    events.forEach((event) => {
      (event.genres || []).forEach((genre) => {
        if (genre) {
          values.add(genre.toLowerCase());
        }
      });
    });
    return Array.from(values).sort();
  }, [events]);

  const filteredEvents = useMemo(() => {
    const list = selectedTags.size === 0
      ? events
      : events.filter((event) => {
          const eventTags = (event.genres || []).map((g) => g.toLowerCase());
          return Array.from(selectedTags).some((tag) => eventTags.includes(tag));
        });

    return [...list].sort((a, b) => {
      const aTime = new Date(a.date).getTime();
      const bTime = new Date(b.date).getTime();
      return sortOrder === 'asc' ? aTime - bTime : bTime - aTime;
    });
  }, [events, selectedTags, sortOrder]);

  const pageSize = 12;
  const totalPages = Math.max(1, Math.ceil(filteredEvents.length / pageSize));
  const safePage = Math.min(currentPage, totalPages);
  const paginatedEvents = filteredEvents.slice(
    (safePage - 1) * pageSize,
    safePage * pageSize
  );
  const showPagination = filteredEvents.length > pageSize;
  const renderPagination = (className = '') => (
    <div className={`flex items-center gap-2 ${className}`.trim()}>
      <button
        onClick={() => setCurrentPage((prev) => Math.max(1, prev - 1))}
        disabled={safePage === 1}
        className={`px-3 py-1 text-[11px] font-black uppercase border-2 transition-all nb-button ${
          safePage === 1 
            ? 'bg-[#2a2a2a] text-white/20 cursor-not-allowed border-gray-600 shadow-none transform-none' 
            : 'bg-black text-white border-white hover:bg-[#a1ff00] hover:text-black'
        }`}
      >
        Prev
      </button>
      <div className="text-[11px] font-black uppercase text-white/70">
        Page {safePage} / {totalPages}
      </div>
      <button
        onClick={() => setCurrentPage((prev) => Math.min(totalPages, prev + 1))}
        disabled={safePage === totalPages}
        className={`px-3 py-1 text-[11px] font-black uppercase border-2 transition-all nb-button ${
          safePage === totalPages 
            ? 'bg-[#2a2a2a] text-white/20 cursor-not-allowed border-gray-600 shadow-none transform-none' 
            : 'bg-black text-white border-white hover:bg-[#a1ff00] hover:text-black'
        }`}
      >
        Next
      </button>
    </div>
  );


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
      <header className="flex justify-between items-center mb-16 px-2">
        <div className="flex items-center gap-4">
          <div className="w-16 h-16 bg-[#a1ff00] p-1">
            <img src="/icon.png" alt="BA Nightlife Logo" className="w-full h-full object-contain" />
          </div>
          <div className="flex items-center gap-4 text-xs font-black uppercase text-white tracking-widest bg-black px-4 py-2 border-2 border-white shadow-[4px_4px_0px_0px_#ffffff]">
            EST. 2026
          </div>
        </div>
        <div className="flex items-center gap-4">
          <CombinedConnectButton />
        </div>
      </header>

      <div className="flex flex-col items-center mb-24 text-center">
        <h1 className="text-8xl md:text-9xl font-black mb-6 tracking-tighter uppercase leading-none italic">
          <span className="bg-[#a1ff00] px-4 border-4 border-white nb-title text-black">Music</span><br/>
          <span className="bg-[#ff3cff] px-4 border-4 border-white nb-title text-white">Events</span>
        </h1>
        <p className="text-2xl font-bold bg-[#a1ff00] px-6 py-2 border-4 border-white rotate-1 mt-4 text-[#ff3cff] shadow-[6px_6px_0px_0px_#ffffff]">
          BUENOS AIRES UNDERGROUND SCENE
        </p>
      </div>

      {!loading && events.length > 0 && (
        <div className="nb-card mb-16 p-6 bg-black">
          <div className="space-y-8">
            <div className="w-full">
              <div className="text-xs font-black uppercase text-white/60 mb-4">Filter by tags</div>
              <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-4 w-full">
                <button
                  onClick={() => setSelectedTags(new Set())}
                  className={`py-3 text-[11px] font-black uppercase border-2 border-white transition-all nb-button w-full ${
                    selectedTags.size === 0 
                      ? 'bg-[#a1ff00] text-black' 
                      : 'bg-[#2a2a2a] text-white/60 hover:bg-[#a1ff00] hover:text-black'
                  }`}
                >
                  All
                </button>
                {tags.map((tag) => (
                  <button
                    key={tag}
                    onClick={() => {
                      setSelectedTags((prev) => {
                        const next = new Set(prev);
                        if (next.has(tag)) {
                          next.delete(tag);
                        } else {
                          next.add(tag);
                        }
                        return next;
                      });
                    }}
                    className={`py-3 text-[11px] font-black uppercase border-2 border-white transition-all nb-button w-full ${
                      selectedTags.has(tag) 
                        ? 'bg-[#a1ff00] text-black' 
                        : 'bg-[#2a2a2a] text-white/60 hover:bg-[#a1ff00] hover:text-black'
                    }`}
                  >
                    {tag}
                  </button>
                ))}
              </div>
            </div>
            
            <div className="w-full flex flex-col md:flex-row md:items-end justify-between gap-6">
              <div className="w-full md:w-auto flex-1">
                <div className="text-xs font-black uppercase text-white/60 mb-4">Sort by date</div>
                <div className="grid grid-cols-2 gap-4 w-full md:max-w-sm">
                  <button
                    onClick={() => setSortOrder('asc')}
                    className={`py-3 text-[11px] font-black uppercase border-2 border-white nb-button w-full ${
                      sortOrder === 'asc' 
                        ? 'bg-[#a1ff00] text-black' 
                        : 'bg-[#2a2a2a] text-white/60 hover:bg-[#a1ff00] hover:text-black'
                    }`}
                  >
                    Soonest
                  </button>
                  <button
                    onClick={() => setSortOrder('desc')}
                    className={`py-3 text-[11px] font-black uppercase border-2 border-white nb-button w-full ${
                      sortOrder === 'desc' 
                        ? 'bg-[#a1ff00] text-black' 
                        : 'bg-[#2a2a2a] text-white/60 hover:bg-[#a1ff00] hover:text-black'
                    }`}
                  >
                    Latest
                  </button>
                </div>
              </div>
              
              <div className="flex flex-col items-end gap-2">
                <div className="text-[11px] font-black uppercase text-white/60">
                  {filteredEvents.length} events
                </div>
                {showPagination && renderPagination()}
              </div>
            </div>
          </div>
        </div>
      )}

      {loading ? (
        <div className="flex justify-center items-center h-64">
          <div className="animate-bounce bg-white text-black p-6 border-4 border-white font-black text-3xl">
            LOADING EVENTS...
          </div>
        </div>
      ) : (
        <>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-12">
          {paginatedEvents.length > 0 ? paginatedEvents.map((event) => (
              <div 
                key={event.id}
                className="nb-card flex flex-col group h-full cursor-pointer transition-all active:scale-[0.98]"
                onClick={() => router.push(`/checkin?event_id=${event.id}`)}
              >
                <div className="h-64 border-b-4 border-white relative">
                  {event.media_url ? (
                    <img src={event.media_url} alt={event.title} className="w-full h-full object-cover grayscale group-hover:grayscale-0 transition-all" />
                  ) : (
                    <div className="w-full h-full bg-[#ff3cff]" />
                  )}
                  <div className="absolute top-4 right-4 bg-black text-white px-4 py-1 font-black text-xs uppercase border-2 border-white z-10">
                    {event.genres?.[0] || 'RAVE'}
                  </div>

                  {/* AI Vibe "Floating Sticker" - Button-like design with rotation */}
                  {event.vibe_description && (
                    <div className="absolute -bottom-6 -left-4 p-4 bg-[#a1ff00] border-[3px] border-white text-black transform rotate-1 transition-all group-hover:-rotate-2 shadow-[3px_3px_0px_0px_#ffffff] z-20 max-w-[80%]">
                      <div className="flex items-center gap-1 mb-1 font-black text-[9px] uppercase tracking-tighter opacity-70">
                        <Sparkles size={10} />
                        Vibe Oracle
                      </div>
                      <p className="text-[11px] font-black italic leading-none line-clamp-2">
                        "{event.vibe_description}"
                      </p>
                    </div>
                  )}
                </div>
                <div className="p-8 flex-1 flex flex-col bg-[#1a1a1a]">
                  {/* Fixed height title container - 2 lines, bottom-aligned */}
                  <div className="h-20 flex flex-col justify-end mb-6">
                    <h3 className="text-3xl font-black uppercase leading-[1.1] line-clamp-2 italic">{event.title}</h3>
                  </div>
                  
                  <div className="space-y-4 mb-8">
                    <div className="flex items-center font-bold text-lg">
                      <Calendar size={20} className="mr-3 fill-[#a1ff00]" />
                      <span className="text-white py-0.5">{formatEventDate(event.date)}</span>
                    </div>
                    <div className="flex items-center font-bold text-lg">
                      <MapPin size={20} className="mr-3 fill-[#ffdb00]" />
                      {event.venue ? (
                        <a
                          href={`https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(event.venue)}`}
                          target="_blank"
                          rel="noreferrer"
                          className="underline decoration-4 decoration-[#ff3cff]"
                          onClick={(e) => e.stopPropagation()}
                        >
                          {event.venue}
                        </a>
                      ) : (
                        <span className="underline decoration-4 decoration-[#ff3cff]">BUENOS AIRES</span>
                      )}
                    </div>
                  </div>
                  
                  <div className="mt-auto flex flex-col gap-4">
                    <div className="grid grid-cols-2 gap-4">
                      <a 
                        href={event.source_link.startsWith('http') ? event.source_link : `https://${event.source_link}`} 
                        target="_blank" 
                        rel="noreferrer"
                        className="nb-button text-center py-4 text-sm bg-[#a1ff00] text-black font-black"
                        onClick={(e) => e.stopPropagation()}
                      >
                        GET TICKETS
                      </a>
                      <a 
                        href={`https://music.youtube.com/search?q=${encodeURIComponent(event.title.split(' - ')[0])}`} 
                        target="_blank" 
                        rel="noreferrer"
                        className="nb-button text-center py-4 text-sm bg-white text-black font-black"
                        onClick={(e) => e.stopPropagation()}
                      >
                        LISTEN
                      </a>
                    </div>
                    
                    <div className="text-center text-[9px] font-black uppercase tracking-widest mt-2 animate-pulse-green">
                      Click card for more details & tips
                    </div>
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
        {showPagination && (
          <div className="mt-12 flex justify-center">
            {renderPagination()}
          </div>
        )}
        </>
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
