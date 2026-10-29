/**
 * Render assistant text with real links and inline images.
 * Tool output often includes Unsplash or Picsum URLs.
 */

const URL_PATTERN = /(https?:\/\/[^\s)]+)/g;

function isImageUrl(url: string): boolean {
  return (
    /picsum\.photos|images\.unsplash\.com|source\.unsplash\.com/i.test(url) ||
    /\.(?:png|jpe?g|gif|webp)(?:\?|$)/i.test(url)
  );
}

export function RichText({ text }: { text: string }) {
  const parts = text.split(URL_PATTERN);
  return (
    <>
      {parts.map((part, index) => {
        if (!part.startsWith("http://") && !part.startsWith("https://")) {
          return <span key={index}>{part}</span>;
        }
        if (isImageUrl(part)) {
          return (
            <span key={index} className="rich-image">
              <a href={part} target="_blank" rel="noreferrer">
                {part}
              </a>
              <img src={part} alt="Image returned by a tool" />
            </span>
          );
        }
        return (
          <a key={index} href={part} target="_blank" rel="noreferrer">
            {part}
          </a>
        );
      })}
    </>
  );
}
