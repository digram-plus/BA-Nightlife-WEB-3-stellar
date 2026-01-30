'use client';

import React, { useState, useEffect } from 'react';
import { useUser, useWallets, useSignOut, useOpenfort, useOAuth, useAuthCallback, RecoveryMethod } from '@openfort/react';
import { OAuthProvider } from '@openfort/openfort-js';
import { LogOut, User, Chrome } from 'lucide-react';

export function OpenfortConnectButton() {
  const { isAuthenticated, user } = useUser();
  const { signOut } = useSignOut();
  const { wallets, activeWallet, createWallet, isCreating: isWalletCreating } = useWallets();
  const { client } = useOpenfort();
  const { storeCredentials, isLoading: isOAuthLoading } = useOAuth();
  
  // Handle the OAuth callback automatically
  useAuthCallback({
    onSuccess: (data) => {
      console.log('[OpenfortDebug] Auth Callback Success:', data);
    },
    onError: (err) => {
      console.error('[OpenfortDebug] Auth Callback Error:', err);
    }
  });

  const [isLoggingIn, setIsLoggingIn] = useState(false);
  const [creationError, setCreationError] = useState<string | null>(null);
  const address = activeWallet?.address || wallets?.[0]?.address;

  // Track state changes for debugging
  useEffect(() => {
    if (typeof window !== 'undefined') {
      const url = new URL(window.location.href);
      const hasAuthParams = url.searchParams.has('openfortAuthProvider') || url.searchParams.has('access_token');
      
      console.log('[OpenfortDebug] State Update:', { 
        isAuthenticated, 
        user, 
        address, 
        isWalletCreating, 
        isOAuthLoading,
        hasAuthParams,
        creationError,
        wallets: wallets?.map(w => ({ id: w.id, address: w.address }))
      });
    }
  }, [isAuthenticated, user, address, isWalletCreating, isOAuthLoading, creationError, wallets]);

  // Handle wallet creation manually
  const handleCreateWallet = async () => {
    console.log('[OpenfortDebug] Manual wallet creation triggered...');
    setCreationError(null);
    try {
      const res = await createWallet({
        recovery: {
          recoveryMethod: RecoveryMethod.PASSWORD,
        },
      });
      
      if (res.error) {
        console.error('[OpenfortDebug] Wallet creation error:', res.error);
        setCreationError(res.error.message || 'Unknown creation error');
      } else {
        console.log('[OpenfortDebug] Wallet created successfully:', res);
      }
    } catch (err: any) {
      console.error('[OpenfortDebug] Wallet creation exception:', err);
      setCreationError(err.message || 'Exception during wallet creation');
    }
  };

  const handleGoogleLogin = async () => {
    console.log('[OpenfortDebug] handleGoogleLogin called.');
    if (!client) {
      console.error('[OpenfortDebug] Openfort client not ready.');
      return;
    }

    setIsLoggingIn(true);
    try {
      // We manually add openfortAuthProvider so useAuthCallback can detect it after redirect
      const callbackUrl = new URL(window.location.origin);
      callbackUrl.searchParams.set('openfortAuthProvider', 'google');
      
      console.log('[OpenfortDebug] Requesting OAuth URL with redirect:', callbackUrl.toString());
      
      const redirectUrl = await client.auth.initOAuth({
        provider: OAuthProvider.GOOGLE,
        redirectTo: callbackUrl.toString(),
      });

      console.log('[OpenfortDebug] Received redirect URL:', redirectUrl);

      if (redirectUrl && typeof redirectUrl === 'string') {
        window.location.href = redirectUrl;
      } else {
        console.error('[OpenfortDebug] Failed to get valid redirect URL from SDK.');
        setIsLoggingIn(false);
      }
    } catch (err) {
      console.error('[OpenfortDebug] initOAuth exception:', err);
      setIsLoggingIn(false);
    }
  };

  if (isAuthenticated && address) {
    return (
      <div className="flex items-center gap-4">
        <div className="nb-card bg-black px-4 py-2 border-2 border-[#a1ff00] text-[#a1ff00] font-black text-xs uppercase shadow-[4px_4px_0px_0px_#a1ff00]">
          <span className="flex items-center gap-2">
            <User size={14} />
            {address.slice(0, 6)}...{address.slice(-4)}
          </span>
        </div>
        <button
          onClick={() => {
            console.log('[OpenfortDebug] Signing out...');
            signOut();
          }}
          className="nb-button bg-[#ff3cff] p-2 text-white border-2 border-white shadow-[4px_4px_0px_0px_#ffffff] transition-all active:translate-x-[2px] active:translate-y-[2px] active:shadow-none"
          title="Sign Out"
        >
          <LogOut size={18} />
        </button>
      </div>
    );
  }

  if (isLoggingIn || (isAuthenticated && !address)) {
    return (
      <div className="flex flex-col items-end gap-2">
        <button
          onClick={!isWalletCreating && !creationError ? handleCreateWallet : undefined}
          disabled={isWalletCreating}
          className={`nb-button ${creationError ? 'bg-red-500 text-white' : 'bg-[#a1ff00] text-black'} px-8 py-3 text-sm font-black uppercase shadow-[6px_6px_0px_0px_#ffffff] ${isWalletCreating && 'animate-pulse'}`}
        >
          {creationError ? 'RETRY CREATION' : isWalletCreating ? 'CREATING...' : 'FINISH: CREATE WALLET'}
        </button>
        {creationError && (
          <span className="text-[10px] text-red-500 font-bold uppercase bg-black px-2 py-1 border border-red-500 max-w-[200px] text-right">
            {creationError}
          </span>
        )}
        {!isWalletCreating && !creationError && (
          <span className="text-[10px] text-white font-bold uppercase bg-black px-2 py-1 border-2 border-[#a1ff00]">
            CLICK TO GENERATE SECURE WALLET
          </span>
        )}
      </div>
    );
  }

  return (
    <button
      onClick={handleGoogleLogin}
      className="nb-button bg-[#a1ff00] text-black px-8 py-3 text-sm font-black uppercase shadow-[6px_6px_0px_0px_#ffffff] hover:translate-x-[2px] hover:translate-y-[2px] hover:shadow-[4px_4px_0px_0px_#ffffff] transition-all"
    >
      <div className="flex items-center gap-3">
        <Chrome size={18} />
        GO WITH GOOGLE
      </div>
    </button>
  );
}
