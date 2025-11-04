import type { Metadata } from 'next';
import './globals.css';
import { AuthProvider } from '@/lib/store';

export const metadata: Metadata = {
  title: 'Sistema de Memorándums',
  description: 'Sistema de gestión de memorándums internos',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="es">
      <body>
        <AuthProvider>
          {children}
        </AuthProvider>
      </body>
    </html>
  );
}

