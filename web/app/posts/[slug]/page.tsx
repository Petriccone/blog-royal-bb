import { notFound } from "next/navigation";
import { getAllPosts, getPostBySlug } from "../../../lib/posts";

interface PostPageProps {
  params: { slug: string };
}

export async function generateStaticParams() {
  const posts = await getAllPosts();
  return posts.map((post) => ({ slug: post.slug }));
}

export default async function PostPage({ params }: PostPageProps) {
  const post = await getPostBySlug(params.slug);
  if (!post) return notFound();

  return (
    <article className="post-page">
      <header className="post-page-header">
        <div className="post-page-meta">{post.sourceLabel}</div>
        <h1 className="post-page-title">{post.title}</h1>
        <p className="post-page-summary">{post.summary}</p>
        <div className="post-page-meta-row">
          <span>{post.dateFormatted}</span>
          <span>•</span>
          <span>Leitura crítica sobre água e saúde</span>
        </div>
      </header>

      {post.image && (
        <div className="post-page-cover">
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img src={post.image} alt={post.title} />
        </div>
      )}

      <div
        className="post-page-content"
        dangerouslySetInnerHTML={{ __html: post.html }}
      />

      <footer className="post-page-footer">
        <p>
          Este conteúdo é educativo e não substitui avaliação individualizada
          com profissionais de saúde.
        </p>
        <p>
          Artigo derivado de análise crítica de materiais públicos sobre água,
          hidratação e qualidade da água, com foco em filtros e purificação.
        </p>
      </footer>
    </article>
  );
}

