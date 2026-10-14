export const isValidEmail = (email: string) => /\S+@\S+\.\S+/.test(email);

export const safeRedirect = (target: string, fallback: string = "/dashboard"): string => {
  // Must be a string
  if (typeof target !== "string") return fallback;

  // Must start with a single "/", not "//" or "/\\"
  if (!target.startsWith("/") || target.startsWith("//") || target.startsWith("/\\")) return fallback;

  // Must not contain "\\", "://" or control characters
  if (target.includes("\\")) return fallback;
  if (target.includes("://")) return fallback;
  // Check for control characters (ASCII 0-31 and 127)
  for (let i = 0; i < target.length; i++) {
    const code = target.charCodeAt(i);
    if (code < 32 || code === 127) return fallback;
  }

  // Valid in-app path - return it
  return target;
};
