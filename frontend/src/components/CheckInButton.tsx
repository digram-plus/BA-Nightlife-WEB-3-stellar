'use client';

import React, { useEffect, useState } from 'react';
import { useAccount, useSignMessage } from 'wagmi';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

type CheckInStatus = 'idle' | 'loading' | 'checked' | 'error';

interface CheckInButtonProps {
  eventId: number;
}

export function CheckInButton({ eventId }: CheckInButtonProps) {
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
    ? 'CONNECT WALLET TO CHECK-IN'
    : status === 'loading'
    ? 'SIGNING...'
    : status === 'checked'
    ? 'CHECK-IN CONFIRMED'
    : 'CHECK-IN (SIGN MESSAGE)';

  return (
    <div className="flex flex-col gap-2">
      <button
        onClick={handleCheckIn}
        disabled={disabled}
        className="nb-button w-full flex items-center justify-center py-3 bg-[#ffdb00] text-sm"
      >
        {buttonLabel}
      </button>
      <div className="border-2 border-white px-3 py-2 text-[10px] uppercase font-black">
        OFF-CHAIN PROOF VIA WALLET SIGNATURE
      </div>
      {status === 'error' && error && (
        <div className="text-xs text-red-300 font-bold">{error}</div>
      )}
      {status === 'checked' && checkedAt && (
        <div className="text-[10px] text-white/70 font-mono">Checked-in at {checkedAt}</div>
      )}
    </div>
  );
}
