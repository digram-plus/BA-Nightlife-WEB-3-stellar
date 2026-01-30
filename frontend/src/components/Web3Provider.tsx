'use client';

import * as React from 'react';
import '@rainbow-me/rainbowkit/styles.css';
import {
  getDefaultConfig,
  RainbowKitProvider,
  darkTheme,
} from '@rainbow-me/rainbowkit';
import { WagmiProvider } from 'wagmi';
import { bsc, bscTestnet, opBNB, opBNBTestnet, avalanche, avalancheFuji } from 'wagmi/chains';
import { QueryClientProvider, QueryClient } from '@tanstack/react-query';

import { AuthProvider, OpenfortProvider, RecoveryMethod } from '@openfort/react';
import { AccountTypeEnum } from '@openfort/openfort-js';

const walletConnectProjectId =
  process.env.NEXT_PUBLIC_WALLETCONNECT_PROJECT_ID ?? '';

const openfortPublishableKey =
  process.env.NEXT_PUBLIC_OPENFORT_PUBLISHABLE_KEY ?? '';

const shieldPublishableKey =
  process.env.NEXT_PUBLIC_SHIELD_PUBLISHABLE_KEY ?? '';

if (!walletConnectProjectId) {
  console.warn(
    'Missing NEXT_PUBLIC_WALLETCONNECT_PROJECT_ID. WalletConnect may not work correctly.'
  );
}

if (!openfortPublishableKey || !shieldPublishableKey) {
  console.warn(
    'Missing Openfort or Shield publishable keys. Embedded wallet will not work correctly.'
  );
}

const config = getDefaultConfig({
  appName: 'BA Nightlife',
  projectId: walletConnectProjectId,
  chains: [bscTestnet, opBNBTestnet, bsc, opBNB, avalanche, avalancheFuji],
  ssr: true,
});

const queryClient = new QueryClient();

export function Web3Provider({ children }: { children: React.ReactNode }) {
  return (
    <WagmiProvider config={config}>
      <QueryClientProvider client={queryClient}>
        <OpenfortProvider
          publishableKey={openfortPublishableKey}
          walletConfig={{
            shieldPublishableKey: shieldPublishableKey,
            accountType: AccountTypeEnum.EOA,
            recoverWalletAutomaticallyAfterAuth: false,
          }}
          uiConfig={{
            authProviders: [
              AuthProvider.GOOGLE,
              AuthProvider.EMAIL_OTP,
              AuthProvider.WALLET,
            ],
            enforceSupportedChains: false,
            walletRecovery: {
              allowedMethods: [RecoveryMethod.PASSWORD],
              defaultMethod: RecoveryMethod.PASSWORD,
            },
          }}
        >
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
        </OpenfortProvider>
      </QueryClientProvider>
    </WagmiProvider>
  );
}
