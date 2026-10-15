import React, { useState, useEffect } from 'react';

type CookieCategory = 'essential' | 'analytics' | 'marketing';

interface CookieSettings {
  essential: boolean;
  analytics: boolean;
  marketing: boolean;
}

interface CookieConsentState {
  hasConsented: boolean;
  hasRejected: boolean;
  settings: CookieSettings;
}

const CookieConsentBanner: React.FC = () => {
  const [hasConsented, setHasConsented] = useState<boolean>(false);
  const [hasRejected, setHasRejected] = useState<boolean>(false);
  const [settings, setSettings] = useState<CookieSettings>({
    essential: true,
    analytics: false,
    marketing: false,
  });

  // Simulate loading non-essential scripts only after consent
  useEffect(() => {
    if (hasConsented) {
      // Load analytics/scripts here
      console.log('Analytics loaded with consent');
    }
  }, [hasConsented]);

  const acceptAll = () => {
    setHasConsented(true);
    setHasRejected(false);
    setSettings({ essential: true, analytics: true, marketing: true });
  };

  const rejectAll = () => {
    setHasConsented(false);
    setHasRejected(true);
    setSettings({ essential: true, analytics: false, marketing: false });
  };

  const toggleSetting = (category: CookieCategory) => {
    setSettings(prev => ({
      ...prev,
      [category]: !prev[category],
    }));
  };

  // If rejected, don't show banner
  if (hasRejected) {
    return null;
  }

  // If consented, don't show banner
  if (hasConsented) {
    return null;
  }

  return (
    <div
      aria-label="Cookie consent"
      className="fixed bottom-0 left-0 right-0 z-50 bg-softPaper border-t border-warm-mist px-6 py-3 shadow-lg"
      role="dialog"
      aria-modal="true"
    >
      <div className="max-w-3xl mx-auto flex items-center justify-between">
        <span className="text-sm text-slate-600">
          We use essential cookies to provide the best experience. {' '}
          <a href="/cookies" className="font-medium text-indigo-600 hover:text-indigo-500">
            Learn more
          </a>
        </span>
        <div className="flex gap-3">
          <button
            onClick={rejectAll}
            className="flex-1 py-2 px-4 rounded-lg bg-slate-200 text-slate-600 hover:bg-slate-300 transition-colors text-sm font-medium"
            disabled={settings.analytics && settings.marketing}
          >
            Reject All
          </button>
          <button
            onClick={acceptAll}
            className="flex-1 py-2 px-4 rounded-lg bg-indigo-600 text-white hover:bg-indigo-700 transition-colors text-sm font-medium"
            disabled={!settings.analytics && !settings.marketing}
          >
            Accept All
          </button>
        </div>
      </div>
      <div className="mt-4 flex gap-3 text-xs text-slate-500">
        <div>
          <input
            type="checkbox"
            checked={settings.analytics}
            onChange={() => toggleSetting('analytics')}
            className="rounded border"
          />
          <span>Analytics</span>
        </div>
        <div>
          <input
            type="checkbox"
            checked={settings.marketing}
            onChange={() => toggleSetting('marketing')}
            className="rounded border"
          />
          <span>Marketing</span>
        </div>
      </div>
    </div>
  );
};

export default CookieConsentBanner;