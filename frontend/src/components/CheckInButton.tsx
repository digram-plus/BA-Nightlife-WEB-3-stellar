'use client';

import React, { useEffect, useState } from 'react';
import { useAccount, useSignMessage } from 'wagmi';
import { QRCodeCanvas } from 'qrcode.react';
import { CheckCircle, ShieldCheck } from 'lucide-react';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

type CheckInStatus = 'idle' | 'loading' | 'checked' | 'error';

interface CheckInButtonProps {
  eventId: number;
  source?: string | null;
}

export function CheckInButton({ eventId, source }: CheckInButtonProps) {
  const { address, isConnected } = useAccount();
  const { signMessageAsync } = useSignMessage();
  const [status, setStatus] = useState<CheckInStatus>('idle');
  const [checkedAt, setCheckedAt] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!isConnected || !address) {
      setStatus('idle');
      setCheckedAt(null);
      setError(null);
      return;
    }

    const loadStatus = async () => {
      try {
        const res = await fetch(
          `${API_BASE}/api/checkin/status?event_id=${eventId}&wallet_address=${address}`
        );
        if (!res.ok) {
          return;
        }
        const data = await res.json();
        if (data.status === 'checked_in') {
          setStatus('checked');
          setCheckedAt(data.created_at || null);
        }
      } catch {
        // ignore status fetch errors
      }
    };

    loadStatus();
  }, [address, eventId, isConnected]);

  const handleCheckIn = async () => {
    if (!isConnected || !address) {
      return;
    }
    setStatus('loading');
    setError(null);

    try {
      const challengeRes = await fetch(`${API_BASE}/api/checkin/challenge`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ event_id: eventId }),
      });
      if (!challengeRes.ok) {
        const err = await challengeRes.json().catch(() => ({}));
        throw new Error(err.detail || 'Failed to create check-in challenge');
      }
      const challenge = await challengeRes.json();
      const signature = await signMessageAsync({ message: challenge.message });

      const verifyRes = await fetch(`${API_BASE}/api/checkin/verify`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          event_id: eventId,
          wallet_address: address,
          signature,
          message: challenge.message,
          nonce: challenge.nonce,
        }),
      });

      const payload = await verifyRes.json().catch(() => ({}));
      if (!verifyRes.ok) {
        throw new Error(payload.detail || 'Check-in failed');
      }

      setStatus('checked');
      setCheckedAt(payload.created_at || null);
    } catch (err) {
      setStatus('error');
      setError(err instanceof Error ? err.message : 'Check-in failed');
    }
  };

  const disabled = !isConnected || status === 'loading' || status === 'checked';
  const buttonLabel = !isConnected
    ? 'CONNECT WALLET'
    : status === 'loading'
    ? 'SIGNING...'
    : status === 'checked'
    ? 'CHECK-IN CONFIRMED'
    : source === 'admin'
    ? 'CONFIRM ATTENDANCE'
    : 'CHECK-IN ON SITE (QR)';

  const buttonClass = !isConnected 
    ? "bg-[#ffdb00] text-black" 
    : status === 'checked' 
    ? "bg-[#a1ff00] text-black" 
    : "bg-black text-[#a1ff00] border-2 border-[#a1ff00] shadow-[3px_3px_0px_0px_#a1ff00]";

  if (status === 'checked') {
    const verificationUrl = typeof window !== 'undefined' 
      ? `${window.location.origin}/verify?event_id=${eventId}&wallet_address=${address}`
      : `/verify?event_id=${eventId}&wallet_address=${address}`;

    return (
      <div className="flex flex-col items-center animate-in zoom-in-95 duration-500">
        <div className="nb-card p-6 bg-white mb-6 flex flex-col items-center w-full">
          <div className="mb-4 flex items-center gap-2 text-black font-black uppercase text-xs">
            <ShieldCheck size={18} className="text-[#a1ff00] fill-black" />
            Vibe Verified Proof
          </div>
          <div className="bg-white p-2 border-4 border-black mb-4">
            <QRCodeCanvas 
              value={verificationUrl} 
              size={180}
              level="H"
              includeMargin={false}
            />
          </div>
          <div className="text-[10px] font-mono text-black/50 break-all text-center">
            {address}
          </div>
        </div>
        
        <div className="flex items-center gap-3 bg-[#a1ff00] text-black px-6 py-4 border-4 border-black shadow-[4px_4px_0px_0px_#ffffff] w-full justify-center">
          <CheckCircle size={24} />
          <span className="font-black uppercase italic">Checked-In On-Site</span>
        </div>
        
        <p className="text-[10px] font-black uppercase text-white/40 mt-4 text-center tracking-widest">
          Show this QR to staff if required for perks
        </p>
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-2">
      <button
        onClick={handleCheckIn}
        disabled={disabled && isConnected}
        className={`nb-button w-full flex items-center justify-center py-4 text-xs font-black uppercase ${buttonClass}`}
      >
        {buttonLabel}
      </button>
      {status === 'error' && error && (
        <div className="text-xs text-red-300 font-bold">{error}</div>
      )}
    </div>
  );
}
