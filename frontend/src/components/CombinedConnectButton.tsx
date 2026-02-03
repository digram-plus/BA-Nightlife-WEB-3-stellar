'use client';

import React, { useState, useRef, useEffect } from 'react';
import { useUser, useWallets, useSignOut, useOpenfort, useOAuth, useAuthCallback, RecoveryMethod } from '@openfort/react';
import { OAuthProvider } from '@openfort/openfort-js';
import { ChevronDown, LogOut, User, Chrome, ShieldCheck, X } from 'lucide-react';

export function CombinedConnectButton() {
  const [isOpen, setIsOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);
  
  // Openfort hooks
  const { isAuthenticated: isOpenfortAuthenticated, user: openfortUser } = useUser();
  const { signOut: openfortSignOut } = useSignOut();
  const { wallets, activeWallet, createWallet, isCreating: isWalletCreating } = useWallets();
  const { client: openfortClient } = useOpenfort();
  const { isLoading: isOAuthLoading } = useOAuth();

  // State for Openfort creation flow
  const [isLoggingIn, setIsLoggingIn] = useState(false);
  const [creationError, setCreationError] = useState<string | null>(null);
  const [recoveryPassword, setRecoveryPassword] = useState('');
  
  const openfortAddress = activeWallet?.address || wallets?.[0]?.address;

  // Handle OAuth callback
  useAuthCallback({
    onSuccess: (data) => console.log('[OpenfortDebug] Auth Success:', data),
    onError: (err) => console.error('[OpenfortDebug] Auth Error:', err)
  });

  // Close dropdown on click outside
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const handleGoogleLogin = async () => {
    if (!openfortClient) return;
    setIsLoggingIn(true);
    try {
      const callbackUrl = new URL(window.location.origin);
      callbackUrl.searchParams.set('openfortAuthProvider', 'google');
      const redirectUrl = await openfortClient.auth.initOAuth({
        provider: OAuthProvider.GOOGLE,
        redirectTo: callbackUrl.toString(),
      });
      if (redirectUrl && typeof redirectUrl === 'string') {
        window.location.href = redirectUrl;
      }
    } catch (err) {
      console.error(err);
      setIsLoggingIn(false);
    }
  };

  const handleCreateWallet = async () => {
    setCreationError(null);
    if (!recoveryPassword.trim()) {
      setCreationError('Enter password');
      return;
    }
    try {
      const res = await createWallet({
        recovery: {
          recoveryMethod: RecoveryMethod.PASSWORD,
          password: recoveryPassword.trim(),
        },
      });
      if (res.error) setCreationError(res.error.message || 'Error');
    } catch (err: any) {
      setCreationError(err.message || 'Error');
    }
  };

  // If user is logged in via Google but has no wallet, show the creation flow overlay or inline
  const showCreationFlow = isOpenfortAuthenticated && !openfortAddress;

  if (isOpenfortAuthenticated && openfortAddress) {
    return (
      <div className="flex items-center gap-2">
        <div className="nb-card bg-black px-4 py-2 border-2 border-[#a1ff00] text-[#a1ff00] font-black text-xs uppercase shadow-[4px_4px_0px_0px_#a1ff00]">
          <span className="flex items-center gap-2">
            <User size={14} />
            {openfortAddress.slice(0, 6)}...{openfortAddress.slice(-4)}
          </span>
        </div>
        <button
          onClick={() => openfortSignOut()}
          className="nb-button bg-[#ff3cff] p-2 text-white border-2 border-white shadow-[4px_4px_0px_0px_#ffffff]"
        >
          <LogOut size={18} />
        </button>
      </div>
    );
  }

  return (
    <div className="relative" ref={dropdownRef}>
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="nb-button bg-[#a1ff00] text-black px-6 py-3 text-sm font-black uppercase shadow-[6px_6px_0px_0px_#ffffff] flex items-center gap-2"
      >
        {isOAuthLoading || isLoggingIn ? 'LOGGING IN...' : 
         isWalletCreating ? 'CREATING...' : 
         showCreationFlow ? 'FINISH WALLET' : 'CONNECT WALLET'}
        <ChevronDown className={`transition-transform duration-200 ${isOpen ? 'rotate-180' : ''}`} size={18} />
      </button>

      {isOpen && (
        <div className="absolute top-full mt-4 right-0 w-72 bg-black border-4 border-white shadow-[8px_8px_0px_0px_#ffffff] z-[100] p-4 flex flex-col gap-4">
          <div className="text-[10px] font-black uppercase text-white/50 mb-2 border-b border-white/20 pb-2">
            Select Connection Method
          </div>
          
          {showCreationFlow ? (
            <div className="flex flex-col gap-3">
              <div className="flex items-center gap-2 text-[#a1ff00] font-black text-xs uppercase">
                <ShieldCheck size={16} />
                Secure your wallet
              </div>
              <input
                type="password"
                value={recoveryPassword}
                onChange={(e) => setRecoveryPassword(e.target.value)}
                placeholder="Set recovery password"
                className="nb-card bg-black text-white border-2 border-[#a1ff00] px-3 py-2 text-xs font-bold uppercase"
              />
              <button
                onClick={handleCreateWallet}
                disabled={isWalletCreating}
                className="nb-button bg-[#a1ff00] text-black py-3 text-xs font-black uppercase w-full"
              >
                {isWalletCreating ? 'CREATING...' : 'FINISH: CREATE WALLET'}
              </button>
              {creationError && <div className="text-red-500 text-[9px] font-black uppercase">{creationError}</div>}
            </div>
          ) : (
            <>
              <button
                onClick={handleGoogleLogin}
                className="nb-button bg-white text-black py-4 text-xs font-black uppercase flex items-center justify-center gap-3 hover:bg-[#a1ff00] transition-colors"
              >
                <Chrome size={18} />
                Login with Google
              </button>

              <div className="text-[10px] font-black uppercase text-white/50 text-center">
                Embedded Openfort wallet — no extension required.
              </div>
            </>
          )}
        </div>
      )}
    </div>
  );
}
