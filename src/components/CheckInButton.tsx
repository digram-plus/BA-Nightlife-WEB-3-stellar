'use client';

import React from 'react';

interface CheckInButtonProps {
  eventId: number;
}

export function CheckInButton({ eventId: _eventId }: CheckInButtonProps) {
  return (
    <div className="flex flex-col gap-2">
      <button
        disabled
        className="nb-button w-full flex items-center justify-center py-4 text-xs font-black uppercase bg-[#2a2a2a] text-white/40 border-white/10 cursor-not-allowed"
      >
        CHECK-IN COMING SOON
      </button>
      <div className="text-[10px] font-black uppercase text-white/40 tracking-widest text-center">
        Off-chain check-in is disabled on this release.
      </div>
    </div>
  );
}
