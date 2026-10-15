const useDocumentTitle = (title: string,? canonicalPath?: string) => {
  useEffect(() => {
    // Set document title
    const formattedTitle = title.trim() || 'OmniAgent AI';
    document.title = `${formattedTitle} | OmniAgent AI`;

    // Set canonical URL if canonicalPath is provided
    if (canonicalPath) {
      // Remove existing canonical links
      const existingCanonicals = document.querySelectorAll('link[rel="canonical"]');
      existingCanonicals.forEach(el => el.remove());

      // Build canonical URL: site URL + path (exclude root for cleaner URLs)
      const siteUrl = 'https://omniagent.ai';
      const canonicalPath = canonicalPath === '/' ? '' : canonicalPath;
      const canonicalUrl = canonicalPath ? `${siteUrl}${canonicalPath}` : siteUrl;

      const canonicalLink = document.createElement('link');
      canonicalLink.rel = 'canonical';
      canonicalLink.href = canonicalUrl;
      document.head.appendChild(canonicalLink);
    }
  }, [title, canonicalPath]);
};

export default useDocumentTitle;