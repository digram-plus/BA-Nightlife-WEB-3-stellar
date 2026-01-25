'use client';

import React from 'react';
import { useSendTransaction, useWaitForTransactionReceipt } from 'wagmi';
import { parseEther } from 'viem';
import { Coins } from 'lucide-react';

interface TipButtonProps {
  walletAddress: string;
  artistName: string;
}

export function TipButton({ walletAddress, artistName }: TipButtonProps) {
  const { 
    data: hash, 
    isPending, 
    sendTransaction 
  } = useSendTransaction();

  const { isLoading: isConfirming, isSuccess } = useWaitForTransactionReceipt({ 
    hash, 
  });

  const handleTip = () => {
    if (!walletAddress) return;
    
    // For BNB Hackathon, we send native BNB
    sendTransaction({
      to: walletAddress as `0x${string}`,
      value: parseEther('0.001'), // Default 0.001 BNB (~$0.60 USD)
    });
  };

  if (!walletAddress) return null;

  return (
    <div className="mt-4">
      <button
        onClick={handleTip}
        disabled={isPending || isConfirming}
        className="nb-button w-full flex items-center justify-center py-4 bg-[#ffdb00]"
      >
        <Coins size={20} className="mr-3" />
        {isPending || isConfirming ? 'SENDING...' : `TIP 0.001 BNB`}
      </button>
      {isSuccess && (
        <p className="bg-black text-[#a1ff00] text-center font-black py-2 mt-4 border-2 border-black rotate-1">
          BNB SENT! VIBES SECURED! 🥂
        </p>
      )}
    </div>
  );
}
