import { useEffect } from 'react';

interface UseDocumentTitleProps {
  canonicalPath?: string;
  title?: string;
  description?: string;
  robots?: string;
}

export const useDocumentTitle = ({
  canonicalPath,
  title,
  description,
  robots,
}: UseDocumentTitleProps) => {
  useEffect(() => {
    const currentPath = canonicalPath || window.location.pathname;
    document.title = title || 'OmniAgent AI';
  }, [canonicalPath, title]);

  useEffect(() => {
    const existingDesc = document.querySelector('meta[name="description"]');
    if (description && existingDesc) {
      (existingDesc as any).setAttribute('content', description);
    } else if (description) {
      const newMeta = document.createElement('meta');
      newMeta.name = 'description';
      newMeta.content = description;
      document.head.appendChild(newMeta);
    }
  }, [description, canonicalPath]);

  useEffect(() => {
    if (robots) {
      const existingRobots = document.querySelector('meta[name="robots"]');
      if (existingRobots) {
        (existingRobots as any).setAttribute('content', robots);
      } else {
        const newRobots = document.createElement('meta');
        newRobots.name = 'robots';
        newRobots.content = robots;
        document.head.appendChild(newRobots);
      }
    }
  }, [robots, canonicalPath]);
};