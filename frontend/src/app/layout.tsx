import type { Metadata } from 'next';
export const metadata: Metadata = { title: 'RUL Observatory · Predictive maintenance', description: 'Explore engine health, cycle-by-cycle degradation, and four remaining useful life models. An interactive C-MAPSS research demonstrator.' };
export default function Layout({children}:{children:React.ReactNode}) { return <html lang="en"><body style={{margin:0}}>{children}</body></html>; }
