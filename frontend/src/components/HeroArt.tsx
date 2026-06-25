// Тематическая иллюстрация для hero: резюме, подобранное под вакансию, и рост совпадения.
export function HeroArt() {
  return (
    <svg
      className="hero-art"
      viewBox="0 0 480 380"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      role="img"
      aria-label="Иллюстрация: адаптация резюме под вакансию"
    >
      <defs>
        <linearGradient id="ha-card" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0" stopColor="#ffffff" />
          <stop offset="1" stopColor="#f1faf4" />
        </linearGradient>
        <linearGradient id="ha-bar" x1="0" y1="1" x2="0" y2="0">
          <stop offset="0" stopColor="#16a34a" />
          <stop offset="1" stopColor="#34d399" />
        </linearGradient>
      </defs>

      {/* плавающие «пузыри» навыков */}
      <g className="ha-float ha-float-1">
        <circle cx="66" cy="74" r="34" fill="#dcfce7" />
        <text x="66" y="86" fontSize="28" textAnchor="middle">🐍</text>
      </g>
      <g className="ha-float ha-float-2">
        <circle cx="414" cy="60" r="30" fill="#d1fae5" />
        <text x="414" y="71" fontSize="26" textAnchor="middle">⚙️</text>
      </g>
      <g className="ha-float ha-float-3">
        <circle cx="430" cy="300" r="32" fill="#fdecd3" />
        <text x="430" y="312" fontSize="28" textAnchor="middle">🚀</text>
      </g>
      <g className="ha-float ha-float-1">
        <circle cx="50" cy="300" r="28" fill="#bbf7d0" />
        <text x="50" y="311" fontSize="24" textAnchor="middle">✍️</text>
      </g>

      {/* лист резюме с прогрессом совпадения */}
      <g>
        <rect x="118" y="86" width="244" height="208" rx="22" fill="url(#ha-card)" stroke="#c6ecd6" strokeWidth="2" />
        <rect x="142" y="112" width="120" height="14" rx="7" fill="#bbf0cf" />
        <rect x="142" y="136" width="78" height="10" rx="5" fill="#d8f3e2" />

        {/* строки опыта */}
        <rect x="142" y="162" width="178" height="8" rx="4" fill="#e6f7ec" />
        <rect x="142" y="178" width="150" height="8" rx="4" fill="#e6f7ec" />

        {/* столбики совпадения навыков */}
        <g>
          <rect x="150" y="244" width="26" height="26" rx="6" fill="#bbf0cf" />
          <rect x="190" y="222" width="26" height="48" rx="6" fill="#86e0a8" />
          <rect x="230" y="196" width="26" height="74" rx="6" fill="url(#ha-bar)" />
          <rect x="270" y="180" width="26" height="90" rx="6" fill="url(#ha-bar)" />
          <rect x="310" y="210" width="26" height="60" rx="6" fill="#86e0a8" />
        </g>
        <path d="M163 248 L203 228 L243 204 L283 186 L323 216" stroke="#15803d" strokeWidth="3" fill="none" strokeLinecap="round" strokeLinejoin="round" />
        <circle cx="283" cy="186" r="6" fill="#fff" stroke="#15803d" strokeWidth="3" />
      </g>

      {/* бейдж «совпадение» */}
      <g className="ha-float ha-float-2">
        <circle cx="356" cy="146" r="26" fill="#0f5132" />
        <path d="M345 146 l8 9 l16 -18" stroke="#fff" strokeWidth="4" fill="none" strokeLinecap="round" strokeLinejoin="round" />
      </g>
    </svg>
  );
}
