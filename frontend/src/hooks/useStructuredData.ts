import { useEffect } from 'react';

interface StructuredDataItem {
  '@context': string;
  '@type': string;
  [key: string]: any;
}

export const useStructuredData = (): void => {
  const pathname = window.location.pathname;
  const siteUrl = import.meta.env.VITE_SITE_URL || 'https://omniagent.ai';

  useEffect(() => {
    const scripts: StructuredDataItem[] = [];

    if (pathname === '/') {
      // Landing page: Organization and SoftwareApplication
      scripts.push({
        '@context': 'https://schema.org',
        '@type': 'Organization',
        name: 'OmniAgent AI',
        description:
          'Enterprise Multimodal AI Employee & Automation Platform',
        url: siteUrl,
        logo: `${siteUrl}/favicon.svg`,
        foundingDate: '2024',
      });
      scripts.push({
        '@context': 'https://schema.org',
        '@type': 'SoftwareApplication',
        name: 'OmniAgent AI',
        description:
          'Enterprise Multimodal AI Employee & Automation Platform',
        url: siteUrl + pathname,
        operatingSystem: 'Web',
        applicationCategory: 'ProductivityApplication',
        textEncoding: 'utf-8',
      });
    } else if (
      pathname === '/dashboard' ||
      pathname === '/chat' ||
      pathname === '/documents' ||
      pathname === '/image-analysis' ||
      pathname === '/knowledge-base' ||
      pathname === '/workflows' ||
      pathname === '/approvals' ||
      pathname === '/agent-runs' ||
      pathname === '/analytics' ||
      pathname === '/integrations' ||
      pathname === '/notifications' ||
      pathname === '/settings' ||
      pathname === '/admin'
    ) {
      // Nested public pages: BreadcrumbList and WebSite
      scripts.push({
        '@context': 'https://schema.org',
        '@type': 'BreadcrumbList',
        itemListElement: [
          { '@type': 'ListItem', position: 1, name: 'OmniAgent AI', item: siteUrl },
          { '@type': 'ListItem', position: 2, name: 'Current Page', item: siteUrl + pathname },
        ],
      });
      scripts.push({
        '@context': 'https://schema.org',
        '@type': 'WebSite',
        name: 'OmniAgent AI',
        url: siteUrl,
        description:
          'Enterprise Multimodal AI Employee & Automation Platform',
        publisher: {
          '@type': 'Organization',
          name: 'OmniAgent AI',
        },
      });
    }

    scripts.forEach((item) => {
      const script = document.createElement('script');
      script.type = 'application/ld+json';
      script.textContent = JSON.stringify(item);
      const existing = document.querySelector(
        'script[type="application/ld+json"]'
      );
      if (existing) {
        existing.parentNode?.replaceChild(script, existing);
      } else {
        document.head.appendChild(script);
      }
    });
  }, [pathname, siteUrl]);
};