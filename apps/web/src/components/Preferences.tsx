import { useEffect, useState } from 'react';

type Preferences = { theme: 'light' | 'dark' | 'system'; size: 'normal' | 'large' };
export function Preferences({ userId }: { userId: string }) {
  const key = `tagger.preferences.${userId}`;
  const [value, setValue] = useState<Preferences>(() => {
    try {
      const saved = JSON.parse(localStorage.getItem(key) || '{}');
      return { theme: ['light', 'dark', 'system'].includes(saved.theme) ? saved.theme : 'system', size: saved.size === 'large' ? 'large' : 'normal' };
    } catch { return { theme: 'system', size: 'normal' }; }
  });
  useEffect(() => {
    document.documentElement.dataset.theme = value.theme;
    document.documentElement.dataset.size = value.size;
    try { localStorage.setItem(key, JSON.stringify(value)); } catch { /* Preferences remain usable without storage. */ }
    return () => { delete document.documentElement.dataset.theme; delete document.documentElement.dataset.size; };
  }, [value, key]);
  return <details className="preferences"><summary>Appearance</summary><div className="preferences-content">
    <label htmlFor="theme-preference">Theme</label><select id="theme-preference" value={value.theme} onChange={e => setValue({ ...value, theme: e.target.value as Preferences['theme'] })}>
      <option value="system">System</option><option value="light">Light</option><option value="dark">Dark</option>
    </select>
    <label htmlFor="text-preference">Interface text</label><select id="text-preference" value={value.size} onChange={e => setValue({ ...value, size: e.target.value as Preferences['size'] })}>
      <option value="normal">Standard</option><option value="large">Large</option>
    </select>
  </div></details>;
}
