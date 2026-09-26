import BrandMark from "./BrandMark";

export default function AuthShell({
  title,
  subtitle,
  children,
  footer,
}) {
  return (
    <main className="auth-page">
      <section className="auth-card">

        <BrandMark />

        <div className="auth-heading">
          <h1>{title}</h1>

          {subtitle && (
            <p>{subtitle}</p>
          )}
        </div>

        <div className="auth-content">
          {children}
        </div>

        {footer && (
          <div className="auth-footer">
            {footer}
          </div>
        )}

      </section>
    </main>
  );
}