// Фирменный логотип CV Tailor: знак «документ + галочка-совпадение» в градиентном бейдже.
export function Logo({ light = false }: { light?: boolean }) {
  return (
    <span className={`brand-logo${light ? " brand-logo--light" : ""}`}>
      <span className="brand-mark" aria-hidden>
        <svg viewBox="0 0 40 40" fill="none" xmlns="http://www.w3.org/2000/svg">
          <defs>
            <linearGradient id="lg-grad" x1="0" y1="0" x2="1" y2="1">
              <stop offset="0" stopColor="#3b82f6" />
              <stop offset="1" stopColor="#0ea5e9" />
            </linearGradient>
          </defs>
          <rect width="40" height="40" rx="12" fill="url(#lg-grad)" />
          {/* лист резюме */}
          <rect x="12" y="9.5" width="16" height="21" rx="3" fill="#ffffff" fillOpacity="0.92" />
          <rect x="15" y="14" width="10" height="2" rx="1" fill="#2563eb" fillOpacity="0.55" />
          <rect x="15" y="18" width="7" height="2" rx="1" fill="#2563eb" fillOpacity="0.35" />
          {/* галочка — «резюме совпало с вакансией» */}
          <circle cx="27" cy="27" r="7.5" fill="#16a34a" />
          <path d="M23.8 27.2 l2.2 2.3 l4.2 -5" stroke="#ffffff" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
      </span>
      <span className="brand-text">
        CV<span className="brand-text-accent">Tailor</span>
      </span>
    </span>
  );
}
