import type { components } from './schema';

export type Project = components['schemas']['Project'];
export type Document = components['schemas']['Document'];
export type Job = components['schemas']['Job'];
export type Member = components['schemas']['Membership'];
export type Audit = components['schemas']['Audit'];
export type Session = components['schemas']['Session'];
export type Page<T> = { count: number; next: string | null; previous: string | null; results: T[] };

let csrf = '';
export async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const headers = new Headers(options.headers);
  if (options.body && !(options.body instanceof FormData)) headers.set('Content-Type', 'application/json');
  if (options.method && options.method !== 'GET') headers.set('X-CSRFToken', csrf);
  const response = await fetch(`/api/v1${path}`, { ...options, headers, credentials: 'same-origin', cache: 'no-store' });
  if (!response.ok) {
    const body = await response.json().catch(() => null);
    const detail = body?.detail ?? (body ? Object.values(body).flat().join(' ') : null);
    throw new Error(typeof detail === 'string' && detail ? detail : 'The request could not be completed. Please try again.');
  }
  return response.status === 204 ? undefined as T : response.json();
}

export async function session(): Promise<Session> {
  const value = await request<Session>('/auth/session/'); csrf = value.csrf_token; return value;
}
export async function signIn(username: string, password: string): Promise<Session> {
  const value = await request<Session>('/auth/login/', { method: 'POST', body: JSON.stringify({ username, password }) });
  csrf = value.csrf_token; return value;
}
export async function signOut(): Promise<void> {
  const value = await request<Session>('/auth/logout/', { method: 'POST' }); csrf = value.csrf_token;
}
export function nextPage<T>(url: string): Promise<Page<T>> {
  const parsed = new URL(url, window.location.origin);
  if (!parsed.pathname.startsWith('/api/v1/')) throw new Error('Invalid pagination link');
  return request<Page<T>>(parsed.pathname.slice('/api/v1'.length) + parsed.search);
}
export function message(error: unknown): string {
  return error instanceof Error ? error.message : 'The request could not be completed.';
}
