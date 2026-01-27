'use client';

import React from 'react';
import { useChainId, useSendTransaction, useWaitForTransactionReceipt } from 'wagmi';
import { parseEther } from 'viem';
import { Coins } from 'lucide-react';
import confetti from 'canvas-confetti';

interface TipButtonProps {
  walletAddress: string;
  artistName: string;
}

export function TipButton({ walletAddress, artistName }: TipButtonProps) {
  const chainId = useChainId();
  const { 
    data: hash, 
    isPending, 
    sendTransaction 
  } = useSendTransaction();

  const { isLoading: isConfirming, isSuccess } = useWaitForTransactionReceipt({ 
    hash, 
  });
 
  React.useEffect(() => {
    if (isSuccess) {
      confetti({
        particleCount: 150,
        spread: 70,
        origin: { y: 0.6 },
        colors: ['#a1ff00', '#ffffff', '#ff3cff']
      });
    }
  }, [isSuccess]);

  const handleTip = () => {
    if (!walletAddress) return;
    
    // For BNB Hackathon, we send native BNB
    sendTransaction({
      to: walletAddress as `0x${string}`,
      value: parseEther('0.001'), // Default 0.001 BNB (~$0.60 USD)
    });
  };

  if (!walletAddress) return null;

  const explorerBaseUrl =
    chainId === 56
      ? 'https://bscscan.com'
      : chainId === 97
      ? 'https://testnet.bscscan.com'
      : chainId === 204
      ? 'https://opbnbscan.com'
      : chainId === 5611
      ? 'https://testnet.opbnbscan.com'
      : 'https://bscscan.com';

  const txUrl = hash ? `${explorerBaseUrl}/tx/${hash}` : null;
  const shortHash = hash ? `${hash.slice(0, 6)}...${hash.slice(-4)}` : null;
  const proofStatus = isPending || isConfirming
    ? 'PENDING'
    : isSuccess
    ? 'CONFIRMED'
    : 'NOT CREATED';

  return (
    <div className="flex flex-col gap-4">
      <button
        onClick={handleTip}
        disabled={isPending || isConfirming}
        className="nb-button w-full flex items-center justify-center py-4 bg-[#a1ff00] text-lg"
      >
        <Coins size={20} className="mr-3" />
        {isPending || isConfirming ? 'SENDING...' : `TIP 0.001 BNB`}
      </button>
      {/* Button-like On-Chain Proof */}
      <a
        href={txUrl || '#'}
        target={txUrl ? "_blank" : "_self"}
        rel="noreferrer"
        className={`nb-button w-full flex flex-col items-center justify-center py-3 !bg-black !text-[#a1ff00] no-underline transition-opacity border-[#a1ff00] ${!txUrl ? 'cursor-default opacity-80' : 'cursor-pointer hover:opacity-100'}`}
      >
        <div className="flex items-center justify-between w-full px-4 text-[10px] font-black uppercase mb-1">
          <span>ON-CHAIN PROOF</span>
          <span className="bg-[#a1ff00] text-black px-1 py-0.5">{proofStatus}</span>
        </div>
        <div className="text-[12px] font-mono font-bold">
          {shortHash ? `TX: ${shortHash}` : 'SEND TIP ABOVE TO CREATE PROOF'}
        </div>
      </a>
      {isSuccess && (
        <div className="bg-black text-[#a1ff00] text-center font-black py-2 mt-4 border-2 border-black rotate-1">
          <p>BNB SENT! VIBES SECURED! 🥂</p>
          {txUrl && (
            <a
              href={txUrl}
              target="_blank"
              rel="noreferrer"
              className="inline-block mt-2 underline text-white"
            >
              VIEW ON EXPLORER
            </a>
          )}
        </div>
      )}
    </div>
  );
}
