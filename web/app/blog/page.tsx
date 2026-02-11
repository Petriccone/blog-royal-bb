import Link from "next/link";
import { getAllPosts } from "../../lib/posts";

export const dynamic = "force-static";

export const metadata = {
  title: "Blog — Artigos | Royal B&B",
  description:
    "Todos os artigos sobre água, filtros, saúde e hidratação. Conteúdo aprofundado para você tomar melhores decisões.",
};

export default async function BlogPage() {
  const posts = await getAllPosts();

  return (
    <>
      <h1 className="sidebar-panel-title" style={{ marginBottom: "1.5rem" }}>
        Todos os artigos
      </h1>
      {posts.length === 0 ? (
        <p style={{ fontSize: "1rem", color: "var(--text-muted)" }}>
          Em breve você encontrará aqui artigos sobre água, saúde e filtragem doméstica.
        </p>
      ) : (
        <div className="post-grid">
          {posts.map((post) => (
            <article key={post.slug} className="post-card">
              {post.image && (
                <div className="post-card-image">
                  {/* eslint-disable-next-line @next/next/no-img-element */}
                  <img src={post.image} alt={post.title} />
                </div>
              )}
              <div className="post-card-body">
                <div className="post-card-meta">{post.sourceLabel}</div>
                <h2 className="post-card-title">
                  <Link href={`/posts/${post.slug}`}>{post.title}</Link>
                </h2>
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
      )}
    </>
  );
}
