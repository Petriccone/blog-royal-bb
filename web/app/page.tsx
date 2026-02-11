import Link from "next/link";
import { getAllPosts } from "../lib/posts";

export const dynamic = "force-static";

export default async function HomePage() {
  const posts = await getAllPosts();

  return (
    <div className="home-layout">
      {/* Hero principal */}
      <section className="home-hero" id="por-que-filtrar">
        <div className="home-hero-content fade-up">
          <p
            style={{
              fontSize: "0.8rem",
              textTransform: "uppercase",
              letterSpacing: "0.08em",
              color: "#7dd3fc",
              fontWeight: 600,
              marginBottom: "0.5rem",
            }}
          >
            Saúde começa pela água que você bebe
          </p>
          <h2 className="home-hero-title">Sua fonte segura de água</h2>
          <p className="home-hero-text">
            Descubra como a qualidade da água impacta sua saúde, entenda as
            tecnologias de filtragem e faça escolhas conscientes para sua família.
          </p>
          <div
            style={{
              marginTop: "1.4rem",
              display: "flex",
              gap: "0.6rem",
              justifyContent: "center",
              flexWrap: "wrap",
            }}
          >
            <Link
              href="#beneficios"
              style={{
                padding: "0.6rem 1.1rem",
                borderRadius: "999px",
                background: "#ffffff",
                color: "#0369a1",
                fontSize: "0.85rem",
                fontWeight: 600,
                border: "1px solid rgba(255,255,255,0.9)",
                boxShadow: "0 8px 18px rgba(15,23,42,0.25)",
              }}
            >
              Saiba mais
            </Link>
            <a
              href="https://www.royalbeb.com.br/"
              target="_blank"
              rel="noopener noreferrer"
              style={{
                padding: "0.6rem 1.1rem",
                borderRadius: "999px",
                border: "1px solid rgba(255,255,255,0.85)",
                color: "#f9fafb",
                fontSize: "0.85rem",
                fontWeight: 500,
                background: "transparent",
              }}
            >
              Guia de filtros
            </a>
          </div>
        </div>
      </section>

      {/* Benefícios — 3 cards futuristas com animações */}
      <section className="benefits-section fade-up fade-up-delay-1" id="beneficios">
        <h2 className="benefits-title">Por que confiar nas nossas recomendações?</h2>
        <div className="trust-cards" id="recomendacoes">
          <article className="trust-card trust-card-1">
            <div className="trust-card-glow" aria-hidden />
            <div className="trust-card-icon" aria-hidden>
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14" />
                <polyline points="22 4 12 14.01 9 11.01" />
              </svg>
            </div>
            <h3 className="trust-card-title">Informação verificada</h3>
            <p className="trust-card-text">
              Conteúdo baseado em estudos e análises técnicas sobre qualidade da água.
            </p>
          </article>
          <article className="trust-card trust-card-2">
            <div className="trust-card-glow" aria-hidden />
            <div className="trust-card-icon" aria-hidden>
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M12 2.69l5.66 5.66a8 8 0 1 1-11.31 0z" />
              </svg>
            </div>
            <h3 className="trust-card-title">Foco em saúde</h3>
            <p className="trust-card-text">
              Priorizamos a saúde da sua família acima de marcas ou produtos.
            </p>
          </article>
          <article className="trust-card trust-card-3">
            <div className="trust-card-glow" aria-hidden />
            <div className="trust-card-icon" aria-hidden>
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <circle cx="12" cy="12" r="10" />
                <path d="M8 12h8M12 8l4 4-4 4" />
              </svg>
            </div>
            <h3 className="trust-card-title">Recomendações claras</h3>
            <p className="trust-card-text">
              Guias de compra simplificados para você decidir sem complicações.
            </p>
          </article>
        </div>
      </section>

      {/* Artigos em destaque */}
      <section id="destaques">
        <h2 className="sidebar-panel-title">Artigos em destaque</h2>
        {posts.length === 0 && (
          <p style={{ fontSize: "1.3 rem", color: "#6b7280" }}>
            Em breve você encontrará aqui artigos aprofundados sobre água,
            saúde e filtragem doméstica.
          </p>
        )}
        <div className="post-grid">
          {posts.slice(0, 4).map((post) => (
            <article key={post.slug} className="post-card">
              {post.image && (
                <div className="post-card-image">
                  {/* eslint-disable-next-line @next/next/no-img-element */}
                  <img src={post.image} alt={post.title} />
                </div>
              )}
              <div className="post-card-body">
                <div className="post-card-meta">{post.sourceLabel}</div>
                <h3 className="post-card-title">
                  <Link href={`/posts/${post.slug}`}>{post.title}</Link>
                </h3>
                <p className="post-card-excerpt line-clamp-3">
                  {post.summary}
                </p>
                <div className="post-card-footer">
                  <span>{post.dateFormatted}</span>
                  <Link href={`/posts/${post.slug}`} className="post-card-link">
                    Ler artigo completo
                  </Link>
                </div>
              </div>
            </article>
          ))}
        </div>
        {posts.length > 0 && (
          <div style={{ marginTop: "1.5rem", textAlign: "center" }}>
            <Link
              href="/blog"
              style={{
                display: "inline-block",
                padding: "0.65rem 1.25rem",
                borderRadius: "var(--radius-sm)",
                background: "linear-gradient(135deg, #0079b8, #00a6d6)",
                color: "#fff",
                fontSize: "0.9rem",
                fontWeight: 600,
              }}
            >
              Ver todos os artigos
            </Link>
          </div>
        )}
      </section>

      {/* Seção de guia / CTA */}
      <section
        id="guia"
        style={{
          marginTop: "2.5rem",
        }}
      >
        <div className="sidebar-panel">
          <h3 className="sidebar-panel-title">
            Não sabe qual filtro escolher?
          </h3>
          <p>
            Estamos preparando um guia comparativo para ajudar você a entender
            as diferenças entre tipos de filtros e encontrar a solução ideal
            para sua casa.
          </p>
          <p style={{ marginTop: "0.5rem" }}>
            Enquanto isso, explore os artigos do blog para aprender mais sobre
            qualidade da água, tecnologias de filtração e hidratação saudável.
          </p>
        </div>
      </section>
    </div>
  );
}

