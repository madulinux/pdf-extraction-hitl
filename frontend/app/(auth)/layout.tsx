/**
 * Auth Layout
 * Layout for authentication pages (login, register)
 * No sidebar, no navbar - clean auth pages
 */
export default function AuthLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="min-h-screen">
      {children}
    </div>
  );
}
