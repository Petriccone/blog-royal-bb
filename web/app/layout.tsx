import "./globals.css";
import type { Metadata } from "next";
import { ReactNode } from "react";

export const metadata: Metadata = {
  title: "Blog Água & Saúde",
  description:
    "Conteúdos profundos sobre saúde, hidratação e qualidade da água, com foco em filtros e purificação doméstica.",
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="pt-BR">
      <body>
        <div className="site-root">
          <header className="site-header">
            <div className="site-header-inner">
              <div className="site-header-left">
                {/* eslint-disable-next-line @next/next/no-img-element */}
                <img
                  src="/logo-royal-bb.png"
                  alt="Blog Royal B&B"
                  className="site-header-logo"
                />
                <div>
                  <h1 className="site-title">Blog Royal B&B</h1>
                </div>
              </div>
              <nav className="site-header-nav">
                <a href="/" style={{ color: "#f9fafb" }}>
                  Home
                </a>
                <a href="#tipos-filtros" style={{ color: "#e5e7eb" }}>
                  Tipos de filtros
                </a>
                <a href="#blog" style={{ color: "#e5e7eb" }}>
                  Blog
                </a>
                <a href="#recomendacoes" style={{ color: "#e5e7eb" }}>
                  Recomendações
                </a>
                <a href="#sobre" style={{ color: "#e5e7eb" }}>
                  Sobre
                </a>
                <a
                  href="#guia"
                  style={{
                    padding: "0.45rem 0.9rem",
                    borderRadius: "999px",
                    background: "linear-gradient(135deg, #00B4DB, #0083B0)",
                    color: "white",
                    fontWeight: 600,
                  }}
                >
                  Guia de compra
                </a>
                <a
                  href="https://www.royalbeb.com.br/"
                  target="_blank"
                  rel="noopener noreferrer"
                  style={{
                    fontWeight: 500,
                    color: "#e5e7eb",
                    borderLeft: "1px solid #374151",
                    paddingLeft: "1.25rem",
                  }}
                >
                  Royal B&B
                </a>
              </nav>
            </div>
          </header>
          <main className="site-main">
            <div className="site-main-inner">{children}</div>
          </main>
          <footer className="site-footer">
            <div className="site-footer-inner">
              <span>
                © {new Date().getFullYear()} Blog Água &amp; Saúde. Todos os
                direitos reservados.
              </span>
              <span>
                Projeto de conteúdo educativo em parceria com{" "}
                <a
                  href="https://www.royalbeb.com.br/"
                  target="_blank"
                  rel="noopener noreferrer"
                  style={{ color: "#93c5fd", fontWeight: 500 }}
                >
                  Royal B&amp;B - Soluções em Filtros
                </a>
                . Não substitui orientação médica profissional.
              </span>
            </div>
          </footer>
        </div>
      </body>
    </html>
  );
}

