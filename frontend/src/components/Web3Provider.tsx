'use client';

import * as React from 'react';
import '@rainbow-me/rainbowkit/styles.css';
import {
  getDefaultConfig,
  RainbowKitProvider,
  darkTheme,
} from '@rainbow-me/rainbowkit';
import { WagmiProvider } from 'wagmi';
import { bsc, bscTestnet, opBNB, opBNBTestnet } from 'wagmi/chains';
import { QueryClientProvider, QueryClient } from '@tanstack/react-query';

const walletConnectProjectId =
  process.env.NEXT_PUBLIC_WALLETCONNECT_PROJECT_ID ?? '';

if (!walletConnectProjectId) {
  console.warn(
    'Missing NEXT_PUBLIC_WALLETCONNECT_PROJECT_ID. WalletConnect may not work correctly.'
  );
}

const config = getDefaultConfig({
  appName: 'BA Nightlife',
  projectId: walletConnectProjectId,
  chains: [bscTestnet, opBNBTestnet, bsc, opBNB],
  ssr: true,
});

const queryClient = new QueryClient();

export function Web3Provider({ children }: { children: React.ReactNode }) {
  return (
    <WagmiProvider config={config}>
      <QueryClientProvider client={queryClient}>
        <RainbowKitProvider
          theme={darkTheme({
            accentColor: '#a1ff00',
            accentColorForeground: 'black',
            borderRadius: 'none',
          })}
          modalSize="compact"
        >
          {children}
        </RainbowKitProvider>
      </QueryClientProvider>
    </WagmiProvider>
  );
}
