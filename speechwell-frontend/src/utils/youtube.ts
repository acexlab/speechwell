/*
File Logic Summary: Helper functions for extracting YouTube video IDs and
building thumbnail URLs without modifying the original video links.
*/

export function extractYouTubeVideoId(url: string): string | null {
  try {
    const parsedUrl = new URL(url);
    const hostname = parsedUrl.hostname.replace(/^www\./, "");

    if (hostname === "youtu.be") {
      const id = parsedUrl.pathname.split("/").filter(Boolean)[0];
      return id || null;
    }

    if (hostname === "youtube.com" || hostname === "m.youtube.com") {
      if (parsedUrl.pathname === "/watch") {
        return parsedUrl.searchParams.get("v");
      }

      const pathParts = parsedUrl.pathname.split("/").filter(Boolean);
      if (pathParts[0] === "embed" || pathParts[0] === "shorts") {
        return pathParts[1] || null;
      }
    }

    return null;
  } catch {
    return null;
  }
}

export function getYouTubeThumbnailUrl(url: string): string | null {
  const videoId = extractYouTubeVideoId(url);
  if (!videoId) return null;
  return `https://img.youtube.com/vi/${videoId}/hqdefault.jpg`;
}

export function getYouTubeEmbedUrl(url: string): string | null {
  const videoId = extractYouTubeVideoId(url);
  if (!videoId) return null;
  return `https://www.youtube.com/embed/${videoId}?rel=0&modestbranding=1`;
}
