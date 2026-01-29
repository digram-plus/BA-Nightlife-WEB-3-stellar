import { NextRequest, NextResponse } from 'next/server';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
const SCRAPE_API_KEY = process.env.SCRAPE_API_KEY || '';

export async function POST(
  _request: NextRequest,
  { params }: { params: Promise<{ source: string }> }
) {
  const { source } = await params;
  if (!SCRAPE_API_KEY) {
    return NextResponse.json(
      { detail: 'SCRAPE_API_KEY not configured' },
      { status: 500 }
    );
  }

  const res = await fetch(`${API_BASE}/api/scrape/${source}`, {
    method: 'POST',
    headers: { 'X-API-Key': SCRAPE_API_KEY },
  });

  const data = await res.json().catch(() => ({}));
  return NextResponse.json(data, { status: res.status });
}
