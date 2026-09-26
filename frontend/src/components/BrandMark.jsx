export default function BrandMark({ size = "medium" }) {
  return (
    <div className={`rhythm-brand rhythm-brand-${size}`}>
      <div className="rhythm-brand-symbol" aria-hidden="true">
        <svg
          viewBox="0 0 48 48"
          fill="none"
          xmlns="http://www.w3.org/2000/svg"
        >
          {/* R / sound-wave mark */}
          <path
            d="M10 35V13H21.5C27.3 13 31 16 31 20.7C31 24.2 28.8 26.5 25.5 27.5L33.5 35"
            stroke="currentColor"
            strokeWidth="3.2"
            strokeLinecap="round"
            strokeLinejoin="round"
          />

          <path
            d="M10 21H21"
            stroke="currentColor"
            strokeWidth="3.2"
            strokeLinecap="round"
          />

          {/* Rhythm waves */}
          <path
            d="M34 17V31"
            stroke="currentColor"
            strokeWidth="3"
            strokeLinecap="round"
          />

          <path
            d="M39 20V28"
            stroke="currentColor"
            strokeWidth="3"
            strokeLinecap="round"
          />

          <path
            d="M44 23V25"
            stroke="currentColor"
            strokeWidth="3"
            strokeLinecap="round"
          />
        </svg>
      </div>

      <span className="rhythm-brand-name">
        RHYTHM
      </span>
    </div>
  );
}