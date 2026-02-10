import fs from "node:fs";
import path from "node:path";
import matter from "gray-matter";
import { remark } from "remark";
import html from "remark-html";

// Como o código roda dentro do app Next em `web/`, o diretório de posts
// fica em `web/content/posts` relativo à raiz do projeto, mas em tempo
// de execução o `process.cwd()` já é `web/`. Por isso não repetimos `web/` aqui.
const contentDir = path.join(process.cwd(), "content", "posts");

export interface PostMeta {
  title: string;
  slug: string;
  date: string;
  dateFormatted: string;
  source: string;
  sourceLabel: string;
  original_url: string;
  summary: string;
  tags: string[];
  image?: string;
  image_cover?: string;
  image_inline?: string;
}

export interface Post extends PostMeta {
  html: string;
}

function toDateFormatted(date: string): string {
  const d = new Date(date);
  if (Number.isNaN(d.getTime())) return date;
  return d.toLocaleDateString("pt-BR", {
    year: "numeric",
    month: "short",
    day: "2-digit",
  });
}

function sourceLabel(source: string): string {
  if (source.includes("superfilter")) return "SuperFilter (análises críticas)";
  if (source.includes("doctoragua")) return "Doctor Agua (análises críticas)";
  return "Conteúdo sobre água & saúde";
}

export async function getAllPosts(): Promise<PostMeta[]> {
  if (!fs.existsSync(contentDir)) return [];

  const files = fs
    .readdirSync(contentDir)
    .filter((file) => file.endsWith(".md"));

  const posts: PostMeta[] = files
    .map((file) => {
      const fullPath = path.join(contentDir, file);
      const fileContents = fs.readFileSync(fullPath, "utf8");
      const { data } = matter(fileContents);

      const slug = String(data.slug || file.replace(/\.md$/, ""));
      const title = String(data.title || slug);
      const date = String(data.date || new Date().toISOString().slice(0, 10));
      const source = String(data.source || "desconhecida");
      const summary = String(
        data.summary || "Artigo sobre água, filtros e saúde."
      );
      const tags = (data.tags as string[]) || [];
      const image_cover = (data.image_cover ||
        data.image) as string | undefined;
      const image_inline = data.image_inline as string | undefined;
      const image = image_cover || image_inline;
      const original_url = String(data.original_url || "");

      return {
        title,
        slug,
        date,
        dateFormatted: toDateFormatted(date),
        source,
        sourceLabel: sourceLabel(source),
        original_url,
        summary,
        tags,
        image,
        image_cover,
        image_inline,
      };
    })
    .sort((a, b) => (a.date < b.date ? 1 : -1));

  return posts;
}

export async function getPostBySlug(slug: string): Promise<Post | null> {
  if (!fs.existsSync(contentDir)) return null;
  const filePath = path.join(contentDir, `${slug}.md`);
  if (!fs.existsSync(filePath)) return null;

  const fileContents = fs.readFileSync(filePath, "utf8");
  const { data, content } = matter(fileContents);

  const metaList = await getAllPosts();
  const baseMeta =
    metaList.find((p) => p.slug === slug) ||
    ({
      title: data.title || slug,
      slug,
      date: data.date || new Date().toISOString().slice(0, 10),
      dateFormatted: toDateFormatted(
        data.date || new Date().toISOString().slice(0, 10)
      ),
      source: data.source || "desconhecida",
      sourceLabel: sourceLabel(String(data.source || "desconhecida")),
      original_url: data.original_url || "",
      summary: data.summary || "",
      tags: (data.tags as string[]) || [],
      image:
        (data.image_cover || data.image) as string | undefined,
      image_cover: data.image_cover as string | undefined,
      image_inline: data.image_inline as string | undefined,
    } as PostMeta);

  const processed = await remark().use(html).process(content);
  const htmlContent = processed.toString();

  return {
    ...baseMeta,
    html: htmlContent,
  };
}

